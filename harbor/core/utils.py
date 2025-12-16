from __future__ import annotations

import ast
import io
import hashlib
import tokenize
from pathlib import Path
from typing import List, Optional


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
