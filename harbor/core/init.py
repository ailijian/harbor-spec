from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any, Optional

import yaml


class Initializer:
    def __init__(self, cwd: Optional[Path] = None) -> None:
        self.cwd = cwd or Path.cwd()
        self.config_dir = self.cwd / ".harbor"
        self.config_path = self.config_dir / "config.yaml"

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

    def write_config(self, code_roots: List[str], force: bool = False, profile: str = "enforce_l3") -> Path:
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
        payload: Dict[str, Any] = {
            "schema_version": "1.0.2",
            "profile": profile,
            "code_roots": code_roots,
            "exclude_paths": [".venv/**", "tests/**", "build/**", "dist/**", "docs/**"],
        }
        text = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
        self.config_path.write_text(text, encoding="utf-8")
        return self.config_path

