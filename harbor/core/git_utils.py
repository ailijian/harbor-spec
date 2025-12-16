from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pathspec import PathSpec


class GitIgnoreMatcher:
    """Git 风格忽略匹配器。

    功能:
      - 读取项目根目录的 `.gitignore` 并编译成匹配器。
      - 合并 Harbor 配置中的 `exclude_paths` 作为附加忽略模式。
      - 提供文件/目录路径的忽略判断（相对于项目根的 POSIX 路径）。

    使用场景:
      - `IndexBuilder` 在遍历文件树时进行目录剪枝与文件过滤。

    依赖:
      - pathspec.PathSpec (gitwildmatch)
      - .harbor/config.yaml 的 exclude_paths

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only
    """
    def __init__(self, root: Optional[Path] = None, patterns: Optional[List[str]] = None) -> None:
        self.root = root or Path.cwd()
        lines = []
        gitignore = self.root / ".gitignore"
        if gitignore.exists():
            try:
                lines.extend((gitignore.read_text(encoding="utf-8") or "").splitlines())
            except Exception:
                lines.extend([])
        if patterns:
            lines.extend(patterns)
        self.spec = PathSpec.from_lines("gitwildmatch", lines)

    @classmethod
    def from_root(cls, cfg_excludes: Optional[List[str]] = None) -> "GitIgnoreMatcher":
        return cls(root=Path.cwd(), patterns=cfg_excludes or [])

    def match_file(self, rel_path: str) -> bool:
        """判断相对路径文件是否被忽略。

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only

        Args:
          rel_path (str): 项目根相对的 POSIX 文件路径。

        Returns:
          bool: True 表示应忽略。
        """
        return self.spec.match_file(rel_path)

    def match_dir(self, rel_path: str) -> bool:
        """判断相对路径目录是否被忽略（用于剪枝）。

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only

        Args:
          rel_path (str): 项目根相对的 POSIX 目录路径。

        Returns:
          bool: True 表示应忽略。
        """
        p = rel_path if rel_path.endswith("/") else (rel_path + "/")
        return self.spec.match_file(p)
