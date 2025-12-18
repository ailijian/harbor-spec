from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import yaml


@dataclass
class DefaultConfig:
    schema_version: str
    profile: str
    code_roots: List[str]
    exclude_paths: List[str]
    language: str


class ProjectDetector:
    def __init__(self, cwd: Optional[Path] = None) -> None:
        self.cwd = cwd or Path.cwd()

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

        return stacks or ["Python"], code_roots, excludes

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
        self.config_dir = self.cwd / ".harbor"
        self.config_path = self.config_dir / "config.yaml"

    def autodetect(self) -> Tuple[List[str], List[str], List[str]]:
        """高级启发式自动探测。

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only

        Returns:
          Tuple[List[str], List[str], List[str]]: (detected_stacks, code_roots, exclude_paths)
        """
        detector = ProjectDetector(cwd=self.cwd)
        return detector.detect()

    def detect_code_roots(self) -> List[str]:
        """智能探测项目代码根目录。

        功能:
          - 按优先级应用探测规则，输出用于扫描的 `code_roots` 列表。
          - 黑名单目录跳过，避免将非代码目录纳入扫描。
          - 支持 src 布局、平铺包布局与脚本布局的兜底。

        使用场景:
          - `harbor init` 命令自动生成 `.harbor/config.yaml`。

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

    def write_config(self, code_roots: List[str], force: bool = False, profile: str = "enforce_l3", exclude_paths: Optional[List[str]] = None) -> Path:
        """写入 `.harbor/config.yaml`。

        功能:
          - 在 `.harbor/` 目录生成配置文件，包含 `code_roots/exclude_paths/profile`。
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

        Returns:
          Path: 配置文件的路径。
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
            language="auto",
        )
        payload: Dict[str, Any] = {
            "schema_version": cfg.schema_version,
            "profile": cfg.profile,
            "code_roots": cfg.code_roots,
            "exclude_paths": cfg.exclude_paths,
            "language": cfg.language,
            "adopted_roots": [],
        }
        text = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
        self.config_path.write_text(text, encoding="utf-8")
        return self.config_path
