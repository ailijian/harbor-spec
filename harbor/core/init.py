from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

import yaml


@dataclass
class DefaultConfig:
    schema_version: str
    profile: str
    code_roots: List[str]
    exclude_paths: List[str]
    language: str


@dataclass(frozen=True)
class TypeScriptProjectHints:
    detected: bool = False
    package_json: bool = False
    tsconfig_json: bool = False
    package_exports: bool = False
    workspace_markers: List[str] = field(default_factory=list)
    entrypoint_candidates: List[str] = field(default_factory=list)
    recommended_preset: str = "legacy_exported"
    package_name: Optional[str] = None


class ProjectDetector:
    def __init__(self, cwd: Optional[Path] = None) -> None:
        self.cwd = cwd or Path.cwd()
        self.last_warnings: List[str] = []

    def detect(self) -> Tuple[List[str], List[str], List[str]]:
        """启发式探测技术栈并生成配置建议。

        功能:
          - 扫描根目录特征文件，识别 Django/Node/Go/Java/Git。
          - 聚合建议的 code_roots 与 exclude_paths（含 .gitignore 规则映射）。
          - 支持混合栈，去重合并。

        使用场景:
          - `harbor init` 的高级探测逻辑。

        依赖:
          - pathlib.Path

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only

        Returns:
          Tuple[List[str], List[str], List[str]]: (detected_stacks, code_roots, exclude_paths)
        """
        stacks: List[str] = []
        code_roots: List[str] = []
        excludes: List[str] = []
        warnings: List[str] = []

        dj_roots, dj_excl, dj_stack = self._detect_django()
        if dj_stack:
            stacks.append(dj_stack)
            code_roots.extend(dj_roots)
            excludes.extend(dj_excl)

        node_roots, node_excl, node_stack = self._detect_node()
        if node_stack:
            stacks.append(node_stack)
            code_roots.extend(node_roots)
            excludes.extend(node_excl)

        ts_roots, ts_excl, ts_stack = self._detect_typescript()
        if ts_stack:
            stacks.append(ts_stack)
            code_roots.extend(ts_roots)
            excludes.extend(ts_excl)

        go_roots, go_excl, go_stack = self._detect_go()
        if go_stack:
            stacks.append(go_stack)
            code_roots.extend(go_roots)
            excludes.extend(go_excl)

        java_roots, java_excl, java_stack = self._detect_java()
        if java_stack:
            stacks.append(java_stack)
            code_roots.extend(java_roots)
            excludes.extend(java_excl)

        py_roots, py_excl, py_stack = self._detect_python_misc()
        if py_stack:
            stacks.append(py_stack)
            code_roots.extend(py_roots)
            excludes.extend(py_excl)

        gi_excl = self._parse_gitignore()
        excludes.extend(gi_excl)

        defaults = self._get_default_excludes()
        excludes.extend(defaults)

        code_roots = self._dedup(code_roots) or ["**/*.py"]
        excludes = self._dedup(excludes)
        excludes = self._filter_excludes(stacks, code_roots, excludes, warnings)
        self.last_warnings = warnings

        return stacks or ["Python"], code_roots, excludes

    def detect_typescript_hints(self) -> TypeScriptProjectHints:
        package_json_path = self.cwd / "package.json"
        package_payload = self._load_package_json()
        package_json_exists = package_json_path.exists()
        tsconfig_exists = (self.cwd / "tsconfig.json").exists() or (self.cwd / "tsconfig.base.json").exists()
        package_exports = self._package_has_exports(package_payload)
        workspace_markers = self._detect_workspace_markers(package_payload)
        entrypoints = self._collect_typescript_entrypoints(package_payload)
        detected = bool(tsconfig_exists or package_exports or entrypoints or self._has_typescript_sources())
        recommended_preset = "legacy_exported"
        if package_exports:
            recommended_preset = "package_public"
        elif entrypoints:
            recommended_preset = "custom_entrypoints"
        package_name = None
        if isinstance(package_payload, dict):
            package_name = str(package_payload.get("name") or "").strip() or None
        return TypeScriptProjectHints(
            detected=detected,
            package_json=package_json_exists,
            tsconfig_json=tsconfig_exists,
            package_exports=package_exports,
            workspace_markers=workspace_markers,
            entrypoint_candidates=entrypoints,
            recommended_preset=recommended_preset,
            package_name=package_name,
        )

    def _normalize_glob(self, pattern: str) -> str:
        p = (pattern or "").strip().replace("\\", "/")
        while p.startswith("./"):
            p = p[2:]
        p = p.lstrip("/")
        return p

    def _is_dangerous_python_exclude(self, pattern: str) -> bool:
        p = self._normalize_glob(pattern)
        return p in {"*.py", "**/*.py"}

    def _exclude_covers_root(self, exclude_pattern: str, root_pattern: str) -> bool:
        ex = self._normalize_glob(exclude_pattern)
        root = self._normalize_glob(root_pattern)
        if not ex or not root:
            return False
        if ex == root:
            return True
        if ex == "." or ex == "**":
            return True
        if ex.endswith("/**"):
            prefix = ex[:-3]
            return bool(prefix) and (root == prefix or root.startswith(prefix + "/"))
        return False

    def _filter_excludes(
        self,
        stacks: List[str],
        code_roots: List[str],
        excludes: List[str],
        warnings: List[str],
    ) -> List[str]:
        is_python = any("python" in (s or "").lower() for s in stacks) or any(
            self._normalize_glob(r).endswith(".py") for r in code_roots
        )
        filtered: List[str] = []
        for raw in excludes:
            pat = self._normalize_glob(raw)
            if is_python and self._is_dangerous_python_exclude(pat):
                warnings.append(f"skip exclude pattern '{raw}' because it may exclude Python sources")
                continue
            conflicted = False
            for root in code_roots:
                if self._exclude_covers_root(pat, root):
                    warnings.append(f"skip exclude pattern '{raw}' because it overlaps code_roots '{root}'")
                    conflicted = True
                    break
            if conflicted:
                continue
            filtered.append(raw)
        return self._dedup(filtered)

    def _detect_django(self) -> Tuple[List[str], List[str], Optional[str]]:
        roots: List[str] = []
        excludes: List[str] = []
        stack = None
        if (self.cwd / "manage.py").exists():
            stack = "Python(Django)"
            apps_glob = "**/apps"
            views_glob = "**/views.py"
            models_glob = "**/models.py"
            roots.extend([apps_glob, views_glob, models_glob])
            excludes.extend(["venv/**", ".venv/**"])
            if not (self.cwd / "src").exists():
                roots.append(".")
        return self._dedup(roots), self._dedup(excludes), stack

    def _detect_node(self) -> Tuple[List[str], List[str], Optional[str]]:
        roots: List[str] = []
        excludes: List[str] = []
        stack = None
        if (self.cwd / "package.json").exists():
            stack = "Node.js"
            excludes.extend(["node_modules/**", "dist/**", ".next/**", "build/**"])
        return roots, self._dedup(excludes), stack

    def _detect_typescript(self) -> Tuple[List[str], List[str], Optional[str]]:
        hints = self.detect_typescript_hints()
        if not hints.detected:
            return [], [], None

        roots: List[str] = []
        src_dir = self.cwd / "src"
        if src_dir.exists() and src_dir.is_dir():
            roots.append("src/**")

        for workspace_root in ("packages", "apps"):
            root_path = self.cwd / workspace_root
            if not root_path.exists() or not root_path.is_dir():
                continue
            for src_path in root_path.glob("*/src"):
                if src_path.exists() and src_path.is_dir():
                    roots.append(f"{src_path.relative_to(self.cwd).as_posix()}/**")

        if not roots:
            for entrypoint in hints.entrypoint_candidates:
                parent = Path(entrypoint).parent.as_posix()
                roots.append("*.ts" if parent in ("", ".") else f"{parent}/**")

        if not roots:
            root_level_ts = [path for path in self.cwd.glob("*.ts") if self._is_typescript_source_file(path)]
            if root_level_ts:
                roots.append("*.ts")

        if not roots:
            roots.append("**/*.ts")

        excludes = ["node_modules/**", "dist/**", ".next/**", "build/**"]
        return self._dedup(roots), self._dedup(excludes), "TypeScript"

    def _detect_go(self) -> Tuple[List[str], List[str], Optional[str]]:
        roots: List[str] = []
        excludes: List[str] = []
        stack = None
        if (self.cwd / "go.mod").exists():
            stack = "Go"
            roots.append(".")
            excludes.append("vendor/**")
        return self._dedup(roots), self._dedup(excludes), stack

    def _detect_java(self) -> Tuple[List[str], List[str], Optional[str]]:
        roots: List[str] = []
        excludes: List[str] = []
        stack = None
        if (self.cwd / "pom.xml").exists() or (self.cwd / "build.gradle").exists():
            stack = "Java"
            roots.append("src/main/java")
            excludes.extend(["target/**", "build/**"])
        return self._dedup(roots), self._dedup(excludes), stack

    def _detect_python_misc(self) -> Tuple[List[str], List[str], Optional[str]]:
        roots: List[str] = []
        excludes: List[str] = []
        stack = None
        if (self.cwd / "requirements.txt").exists() or (self.cwd / "pyproject.toml").exists():
            stack = "Python"
            excludes.extend([".venv/**", "venv/**", "env/**"])
        return self._dedup(roots), self._dedup(excludes), stack

    def _load_package_json(self) -> Optional[Dict[str, Any]]:
        package_json_path = self.cwd / "package.json"
        if not package_json_path.exists():
            return None
        try:
            loaded = json.loads(package_json_path.read_text(encoding="utf-8"))
        except Exception:
            return None
        return loaded if isinstance(loaded, dict) else None

    def _package_has_exports(self, package_payload: Optional[Dict[str, Any]]) -> bool:
        if not isinstance(package_payload, dict):
            return False
        exports = package_payload.get("exports")
        if isinstance(exports, str):
            return bool(exports.strip())
        if isinstance(exports, dict):
            return bool(exports)
        return False

    def _detect_workspace_markers(self, package_payload: Optional[Dict[str, Any]]) -> List[str]:
        markers: List[str] = []
        if isinstance(package_payload, dict) and package_payload.get("workspaces"):
            markers.append("package.json#workspaces")
        for filename in ("pnpm-workspace.yaml", "turbo.json", "nx.json", "lerna.json"):
            if (self.cwd / filename).exists():
                markers.append(filename)
        return self._dedup(markers)

    def _collect_typescript_entrypoints(self, package_payload: Optional[Dict[str, Any]]) -> List[str]:
        candidates: List[str] = []
        for relative_path in ("src/index.ts", "src/public.ts", "index.ts"):
            if (self.cwd / relative_path).exists():
                candidates.append(relative_path)

        if isinstance(package_payload, dict):
            for key in ("source", "types", "typings", "main", "module"):
                mapped = self._resolve_typescript_source_candidate(package_payload.get(key))
                if mapped:
                    candidates.append(mapped)
            for export_target in self._iter_package_export_targets(package_payload.get("exports")):
                mapped = self._resolve_typescript_source_candidate(export_target)
                if mapped:
                    candidates.append(mapped)
        return self._dedup(candidates)

    def _iter_package_export_targets(self, value: Any) -> List[str]:
        targets: List[str] = []
        if isinstance(value, str):
            text = value.strip()
            if text:
                targets.append(text)
            return targets
        if isinstance(value, dict):
            for nested in value.values():
                targets.extend(self._iter_package_export_targets(nested))
        return targets

    def _resolve_typescript_source_candidate(self, raw_value: Any) -> Optional[str]:
        text = str(raw_value or "").strip()
        if not text:
            return None
        normalized = text.replace("\\", "/").lstrip("./")
        candidates = [normalized]
        if normalized.endswith(".d.ts"):
            candidates.append(normalized[:-5] + ".ts")
        if normalized.endswith(".js"):
            candidates.append(normalized[:-3] + ".ts")
            if normalized.startswith("dist/"):
                candidates.append("src/" + normalized[5:-3] + ".ts")
            if normalized.startswith("lib/"):
                candidates.append("src/" + normalized[4:-3] + ".ts")
        for candidate in candidates:
            resolved = self.cwd / candidate
            if resolved.exists() and self._is_typescript_source_file(resolved):
                return candidate
        return None

    def _has_typescript_sources(self) -> bool:
        for path in self.cwd.rglob("*.ts"):
            if self._is_typescript_source_file(path):
                return True
        return False

    def _is_typescript_source_file(self, path: Path) -> bool:
        if not path.is_file():
            return False
        if path.name.endswith(".d.ts"):
            return False
        ignored_dirs = {
            ".git",
            ".harbor",
            ".idea",
            ".next",
            ".venv",
            ".vscode",
            "__pycache__",
            "build",
            "dist",
            "env",
            "htmlcov",
            "node_modules",
            "venv",
        }
        try:
            relative_parts = path.relative_to(self.cwd).parts
        except Exception:
            relative_parts = path.parts
        return not any(part in ignored_dirs for part in relative_parts[:-1])

    def _parse_gitignore(self) -> List[str]:
        gi = self.cwd / ".gitignore"
        out: List[str] = []
        if not gi.exists():
            return out
        try:
            lines = (gi.read_text(encoding="utf-8") or "").splitlines()
        except Exception:
            lines = []
        for raw in lines:
            s = (raw or "").strip()
            if not s or s.startswith("#"):
                continue
            if s.startswith("!"):
                continue
            if s.endswith("/"):
                s = f"{s}**"
            out.append(s)
        return self._dedup(out)

    def _get_default_excludes(self) -> List[str]:
        return [
            ".git/**",
            ".harbor/**",
            ".idea/**",
            ".vscode/**",
            ".venv/**",
            "venv/**",
            "env/**",
            "node_modules/**",
            "__pycache__/**",
            ".mypy_cache/**",
            ".pytest_cache/**",
            ".tox/**",
            "htmlcov/**",
        ]

    def _dedup(self, arr: List[str]) -> List[str]:
        seen: Dict[str, bool] = {}
        out: List[str] = []
        for x in arr:
            k = x
            if k in seen:
                continue
            seen[k] = True
            out.append(x)
        return out


class Initializer:
    def __init__(self, cwd: Optional[Path] = None) -> None:
        self.cwd = cwd or Path.cwd()
        self.config_dir = self.cwd / ".harbor" / "config"
        self.config_path = self.config_dir / "harbor.yaml"
        self.last_warnings: List[str] = []

    def autodetect(self) -> Tuple[List[str], List[str], List[str]]:
        """高级启发式自动探测。

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only

        Returns:
          Tuple[List[str], List[str], List[str]]: (detected_stacks, code_roots, exclude_paths)
        """
        detector = ProjectDetector(cwd=self.cwd)
        stacks, roots, excludes = detector.detect()
        self.last_warnings = list(detector.last_warnings)
        return stacks, roots, excludes

    def detect_typescript_hints(self) -> TypeScriptProjectHints:
        """Detect TypeScript onboarding hints for `harbor init`.

        Behavior:
          - Detects common TypeScript governance signals such as `package.json`,
            `tsconfig.json`, package `exports`, workspace markers, and public
            entrypoint candidates like `src/index.ts`.
          - Recommends one preset for init guidance without mutating config.
          - Stays advisory-first so callers can show guidance before opting in.

        Returns:
          TypeScriptProjectHints: Stable detection summary for init guidance.
        """
        return ProjectDetector(cwd=self.cwd).detect_typescript_hints()

    def detect_code_roots(self) -> List[str]:
        """智能探测项目代码根目录。

        功能:
          - 按优先级应用探测规则，输出用于扫描的 `code_roots` 列表。
          - 黑名单目录跳过，避免将非代码目录纳入扫描。
          - 支持 src 布局、平铺包布局与脚本布局的兜底。

        使用场景:
          - `harbor init` 命令自动生成 `.harbor/config/harbor.yaml`。

        依赖:
          - pathlib.Path

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: once

        Returns:
          List[str]: 由 glob 模式组成的代码根列表。
        """
        blacklist = {
            "tests",
            "docs",
            "build",
            "dist",
            "site-packages",
            "node_modules",
            "venv",
            "env",
        }

        entries = [p for p in self.cwd.iterdir() if p.exists()]
        dirs = [p for p in entries if p.is_dir()]
        files = [p for p in entries if p.is_file()]

        def is_blacklisted_dir(p: Path) -> bool:
            name = p.name
            if name.startswith(".") or name.startswith("__"):
                return True
            if name in blacklist:
                return True
            return False

        src_dir = self.cwd / "src"
        if src_dir.exists() and src_dir.is_dir():
            return ["src/**"]

        code_roots: List[str] = []
        for d in dirs:
            if is_blacklisted_dir(d):
                continue
            init_file = d / "__init__.py"
            if init_file.exists():
                code_roots.append(f"{d.name}/**")

        if code_roots:
            return code_roots

        has_root_py = any(f.suffix == ".py" for f in files)
        if has_root_py:
            return ["*.py"]

        return ["**/*.py"]

    def write_config(
        self,
        code_roots: List[str],
        force: bool = False,
        profile: str = "enforce_l3",
        exclude_paths: Optional[List[str]] = None,
        language: str = "auto",
        advice_mode: str = "basic",
        languages_config: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """写入 `.harbor/config/harbor.yaml`。

        功能:
          - 在 `.harbor/` 目录生成配置文件，包含 `code_roots/exclude_paths/profile`。
          - 允许以 additive 方式写入显式 `languages.*` 配置，例如
            TypeScript governance onboarding 所需的 `languages.typescript`。
          - 写入 advice 配置段：
            - `advice.mode`: `basic|off`
            - `advice.include_in_ci_json`: `true`
            - `advice.include_in_text`: `true`
          - advice 配置与可选 LLM semantic audit 配置解耦：
            `advice=basic` 不需要 LLM，`--no-llm` 不会关闭 deterministic guidance。
          - 若文件已存在且 `force=False`，不覆盖。

        使用场景:
          - `harbor init` 命令的最终写入步骤。

        依赖:
          - yaml.safe_dump

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: once

        Args:
          code_roots (List[str]): 探测得到的代码根列表。
          force (bool): 是否覆盖已有配置。
          profile (str): 配置文件中的默认 profile。
          advice_mode (str): deterministic repair guidance 模式（`basic` 或 `off`）。
          languages_config (Optional[Dict[str, Any]]): 可选语言配置段；缺省时保持旧配置形状。

        Returns:
          Path: 配置文件的路径。

        Side Effects:
          - 仅在 `force`/文件存在策略允许时写入 `.harbor/config/harbor.yaml`。
          - 具体是否写入仍受 init 参数与用户交互选择约束。
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if self.config_path.exists() and not force:
            return self.config_path
        excl = exclude_paths or []
        cfg = DefaultConfig(
            schema_version="1.0.2",
            profile=profile,
            code_roots=code_roots,
            exclude_paths=excl or [
                ".git/**",
                ".harbor/**",
                ".idea/**",
                ".vscode/**",
                ".venv/**",
                "venv/**",
                "env/**",
                "node_modules/**",
            ],
            language=language,
        )
        payload: Dict[str, Any] = {
            "schema_version": cfg.schema_version,
            "profile": cfg.profile,
            "code_roots": cfg.code_roots,
            "exclude_paths": cfg.exclude_paths,
            "language": cfg.language,
            "adopted_roots": [],
            "advice": {
                "mode": "off" if str(advice_mode or "").strip().lower() == "off" else "basic",
                "include_in_ci_json": True,
                "include_in_text": True,
            },
        }
        if isinstance(languages_config, dict) and languages_config:
            payload["languages"] = languages_config
        text = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
        self.config_path.write_text(text, encoding="utf-8")
        return self.config_path
