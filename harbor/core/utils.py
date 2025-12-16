from __future__ import annotations

import ast
import os
import io
import hashlib
import tokenize
from pathlib import Path
from typing import List, Optional

from harbor.core.git_utils import GitIgnoreMatcher


def find_function_node(source: str, lineno: int, name: str) -> Optional[ast.AST]:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and getattr(node, "name", None) == name:
            if getattr(node, "lineno", 0) == lineno:
                return node
    return None


def compute_body_hash(source: str, fn_node: ast.AST) -> str:
    lines = source.splitlines(keepends=True)
    body = ""
    if hasattr(fn_node, "body"):
        stmts = list(getattr(fn_node, "body"))
        if stmts and isinstance(stmts[0], ast.Expr) and isinstance(getattr(stmts[0], "value", None), ast.Constant) and isinstance(stmts[0].value.value, str):
            stmts = stmts[1:]
        chunks: List[str] = []
        for s in stmts:
            start = getattr(s, "lineno", None)
            end = getattr(s, "end_lineno", None)
            if start is None or end is None:
                continue
            seg = "".join(lines[start - 1 : end])
            chunks.append(seg)
        body = "".join(chunks)
    if not body:
        return hashlib.sha256(b"").hexdigest()
    try:
        tokens = tokenize.generate_tokens(io.StringIO(body).readline)
        parts: List[str] = []
        for tok in tokens:
            if tok.type in (
                tokenize.COMMENT,
                tokenize.NL,
                tokenize.NEWLINE,
                tokenize.INDENT,
                tokenize.DEDENT,
                tokenize.ENCODING,
            ):
                continue
            val = tok.string.strip()
            if not val:
                continue
            parts.append(val)
    except (tokenize.TokenError, IndentationError):
        return "0000000000000000000000000000000000000000000000000000000000000000"
    normalized = " ".join(parts)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def iter_project_files(code_roots: List[str], exclude_paths: Optional[List[str]] = None) -> List[Path]:
    """生成待扫描的 Python 文件列表（统一剪枝逻辑）。

    功能:
      - 根据 `code_roots` 计算遍历起点，支持绝对/相对与 glob 模式。
      - 合并 `.gitignore` 与 `exclude_paths` 并进行目录层级剪枝（避免进入大体量无关目录）。
      - 仅返回 `.py` 文件，保证与 IndexBuilder/SyncEngine 行为一致。

    使用场景:
      - IndexBuilder 与 SyncEngine 的文件枚举。

    依赖:
      - GitIgnoreMatcher
      - os.walk

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: read-only

    Args:
      code_roots (List[str]): 代码根路径或模式列表。
      exclude_paths (Optional[List[str]]): 额外排除模式（相对项目根的 gitwildmatch）。

    Returns:
      List[Path]: 去重后的 Python 文件绝对路径列表。
    """
    base = Path.cwd().resolve()
    patterns = code_roots or ["**/*.py"]
    defaults = [".git/**", ".harbor/**", ".venv/**", "venv/**", "env/**", "node_modules/**"]
    cfg_excludes = (exclude_paths or []) + defaults
    matcher = GitIgnoreMatcher.from_root(cfg_excludes=cfg_excludes)
    start_dirs: List[Path] = []
    seed_files: List[Path] = []
    abs_dirs: List[Path] = []
    include_all_dirs = set()
    for pat in patterns:
        p_pat = Path(pat)
        if p_pat.is_absolute():
            if p_pat.is_dir():
                d = p_pat.resolve()
                start_dirs.append(d)
                abs_dirs.append(d)
            elif p_pat.is_file() and p_pat.suffix == ".py":
                seed_files.append(p_pat.resolve())
            continue
        if pat.endswith("/**") or pat.endswith("/**/*.py"):
            prefix = pat.split("/**")[0]
            d = (base / prefix).resolve()
            if d.exists() and d.is_dir():
                start_dirs.append(d)
                include_all_dirs.add(d.as_posix())
        elif "*" in pat:
            start_dirs.append(base)
        else:
            d = (base / pat).resolve()
            if d.exists() and d.is_dir():
                start_dirs.append(d)
            elif d.exists() and d.is_file() and d.suffix == ".py":
                seed_files.append(d)
    sd_seen = {}
    sd_list: List[Path] = []
    for d in start_dirs:
        k = d.as_posix()
        if k in sd_seen:
            continue
        sd_seen[k] = True
        sd_list.append(d)
    files: List[Path] = []
    files.extend(seed_files)
    patterns_rel = [pat for pat in patterns if not Path(pat).is_absolute()]
    for d in sd_list:
        include_all = (d.as_posix() in include_all_dirs) or any(d == x for x in abs_dirs)
        for root, subdirs, filenames in os.walk(d):
            rel_root = Path(root).resolve().relative_to(d.resolve()).as_posix()
            pruned = []
            for s in list(subdirs):
                rel_dir = (Path(rel_root) / s).as_posix() if rel_root else s
                if matcher.match_dir(rel_dir):
                    pruned.append(s)
            if pruned:
                subdirs[:] = [x for x in subdirs if x not in pruned]
            for name in filenames:
                if not name.endswith(".py"):
                    continue
                rel_file = (Path(rel_root) / name).as_posix() if rel_root else name
                if include_all or any(Path(rel_file).match(p) for p in patterns_rel):
                    files.append((Path(root) / name).resolve())
    seen = {}
    dedup: List[Path] = []
    for p in files:
        k = p.as_posix()
        if k in seen:
            continue
        seen[k] = True
        dedup.append(p)
    return dedup
