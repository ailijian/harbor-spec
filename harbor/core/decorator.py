from __future__ import annotations

import ast
import difflib
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Literal, Tuple

from harbor.core.utils import iter_project_files


@dataclass
class Candidate:
    file_path: Path
    func_name: str
    qualified_name: str
    lineno: int
    col_offset: int
    has_docstring: bool
    has_scope_tag: bool
    action: Literal["Keep", "Create", "Skip"]


@dataclass
class DecoratePlan:
    file_path: Path
    description: str
    diff_preview: str
    will_write: bool


@dataclass
class ApplyReport:
    total_candidates: int
    with_docstring: int
    without_docstring: int
    singleline_skipped: int
    changed_files: List[Path]


class DecoratorEngine:
    """智能交互式 Docstring 装饰器引擎。

    功能:
      - 基于 AST 识别候选函数，应用安全/激进策略筛选。
      - 为已有 Docstring 且缺少标签的函数，在闭合引号之前插入 `@harbor.scope: public`。
      - 在激进模式下，为无 Docstring 的函数插入 TODO 模板 Docstring。
      - 生成统一 Diff 预览，并支持干运行或写盘。

    使用场景:
      - `harbor decorate <path> [--strategy safe|aggressive] [--yes] [--dry-run]`。

    依赖:
      - Python 标准库 ast/difflib
      - harbor.core.utils.iter_project_files

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: once

    Args:
      None

    Returns:
      None

    Raises:
      None
    """

    def scan(self, path: str, strategy: Literal["safe", "aggressive"] = "safe") -> List[Candidate]:
        files: List[Path] = []
        p = Path(path)
        if p.is_file() and p.suffix == ".py":
            files = [p.resolve()]
        elif p.is_dir():
            files = iter_project_files([f"{p.as_posix()}/**"], [])
        else:
            files = []
        candidates: List[Candidate] = []
        for fp in files:
            try:
                src = fp.read_text(encoding="utf-8")
            except Exception:
                continue
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            module_qual = self._module_qual_from_path(fp)
            for item in self._extract_functions(tree, module_qual):
                if self._is_filtered_name(item[0]):
                    candidates.append(
                        Candidate(
                            file_path=fp,
                            func_name=item[0],
                            qualified_name=item[1],
                            lineno=item[2],
                            col_offset=item[3],
                            has_docstring=item[4] is not None,
                            has_scope_tag=self._has_scope_tag(item[4]) if item[4] else False,
                            action="Skip",
                        )
                    )
                    continue
                has_doc = item[4] is not None
                has_scope = self._has_scope_tag(item[4]) if item[4] else False
                if strategy == "safe":
                    if has_doc:
                        act: Literal["Keep", "Create", "Skip"] = "Keep" if has_scope else "Keep"
                        candidates.append(
                            Candidate(
                                file_path=fp,
                                func_name=item[0],
                                qualified_name=item[1],
                                lineno=item[2],
                                col_offset=item[3],
                                has_docstring=True,
                                has_scope_tag=has_scope,
                                action=act,
                            )
                        )
                    else:
                        candidates.append(
                            Candidate(
                                file_path=fp,
                                func_name=item[0],
                                qualified_name=item[1],
                                lineno=item[2],
                                col_offset=item[3],
                                has_docstring=False,
                                has_scope_tag=False,
                                action="Skip",
                            )
                        )
                else:
                    act = "Create" if not has_doc else "Keep"
                    candidates.append(
                        Candidate(
                            file_path=fp,
                            func_name=item[0],
                            qualified_name=item[1],
                            lineno=item[2],
                            col_offset=item[3],
                            has_docstring=has_doc,
                            has_scope_tag=has_scope,
                            action=act,
                        )
                    )
        return candidates

    def preview(self, file_path: Path, strategy: Literal["safe", "aggressive"]) -> List[DecoratePlan]:
        try:
            original = file_path.read_text(encoding="utf-8")
        except Exception:
            return []
        try:
            tree = ast.parse(original)
        except SyntaxError:
            return []
        plans: List[DecoratePlan] = []
        lines = original.splitlines(keepends=True)
        changed = False
        out_lines = list(lines)
        edits: List[Tuple[int, List[str]]] = []
        singleline_skipped_local = 0
        for fn in self._iter_function_nodes(tree):
            name = fn.name
            if self._is_filtered_name(name):
                continue
            doc_node = self._docstring_node(fn)
            if doc_node is not None:
                doc_text = ast.get_docstring(fn)
                has_scope = self._has_scope_tag(doc_text) if doc_text else False
                if has_scope:
                    continue
                start = getattr(doc_node, "lineno", None)
                end = getattr(doc_node, "end_lineno", None)
                if start is None or end is None:
                    continue
                if start == end:
                    singleline_skipped_local += 1
                    continue
                closing_idx = end - 1
                indent = self._leading_whitespace(out_lines[closing_idx])
                insert_block = [indent + "\n", indent + "@harbor.scope: public\n"]
                edits.append((closing_idx, insert_block))
                changed = True
            else:
                if strategy == "aggressive":
                    body_start = getattr(fn.body[0], "lineno", getattr(fn, "lineno", 0)) if getattr(fn, "body", None) else getattr(fn, "lineno", 0) + 1
                    insert_idx = max(0, body_start - 1)
                    base_indent = " " * (getattr(fn, "col_offset", 0) + 4)
                    block = [
                        base_indent + '"""TODO: Add summary.\n',
                        "\n",
                        base_indent + "@harbor.scope: public\n",
                        base_indent + '"""\n',
                    ]
                    edits.append((insert_idx, block))
                    changed = True
        if edits:
            for idx, block in sorted(edits, key=lambda x: x[0], reverse=True):
                out_lines[idx:idx] = block
        diff = ""
        if changed:
            new_text = "".join(out_lines)
            diff = "\n".join(
                difflib.unified_diff(
                    original.splitlines(),
                    new_text.splitlines(),
                    fromfile=file_path.as_posix(),
                    tofile=file_path.as_posix(),
                    lineterm="",
                )
            )
        plans.append(
            DecoratePlan(
                file_path=file_path,
                description="Decorate @harbor.scope: public",
                diff_preview=diff,
                will_write=changed,
            )
        )
        return plans

    def apply(self, plans: List[DecoratePlan], dry_run: bool = False, strategy: Literal["safe", "aggressive"] = "safe") -> ApplyReport:
        changed_files: List[Path] = []
        with_doc = 0
        without_doc = 0
        singleline_skipped = 0
        total = 0
        for plan in plans:
            total += 1
            try:
                original = plan.file_path.read_text(encoding="utf-8")
            except Exception:
                continue
            tree = None
            try:
                tree = ast.parse(original)
            except SyntaxError:
                continue
            lines = original.splitlines(keepends=True)
            out_lines = list(lines)
            changed = False
            edits: List[Tuple[int, List[str]]] = []
            for fn in self._iter_function_nodes(tree):
                name = fn.name
                if self._is_filtered_name(name):
                    continue
                doc_node = self._docstring_node(fn)
                if doc_node is not None:
                    with_doc += 1
                    doc_text = ast.get_docstring(fn)
                    has_scope = self._has_scope_tag(doc_text) if doc_text else False
                    if has_scope:
                        continue
                    start = getattr(doc_node, "lineno", None)
                    end = getattr(doc_node, "end_lineno", None)
                    if start is None or end is None:
                        continue
                    if start == end:
                        singleline_skipped += 1
                        continue
                    closing_idx = end - 1
                    indent = self._leading_whitespace(out_lines[closing_idx])
                    insert_block = [indent + "\n", indent + "@harbor.scope: public\n"]
                    edits.append((closing_idx, insert_block))
                    changed = True
                else:
                    without_doc += 1
                    if strategy == "aggressive":
                        body_start = getattr(fn.body[0], "lineno", getattr(fn, "lineno", 0)) if getattr(fn, "body", None) else getattr(fn, "lineno", 0) + 1
                        insert_idx = max(0, body_start - 1)
                        base_indent = " " * (getattr(fn, "col_offset", 0) + 4)
                        block = [
                            base_indent + '"""TODO: Add summary.\n',
                            "\n",
                            base_indent + "@harbor.scope: public\n",
                            base_indent + '"""\n',
                        ]
                        edits.append((insert_idx, block))
                        changed = True
            if edits:
                for idx, block in sorted(edits, key=lambda x: x[0], reverse=True):
                    out_lines[idx:idx] = block
            if plan.will_write and not dry_run and changed:
                new_text = "".join(out_lines)
                plan.file_path.write_text(new_text, encoding="utf-8")
                changed_files.append(plan.file_path)
        return ApplyReport(
            total_candidates=total,
            with_docstring=with_doc,
            without_docstring=without_doc,
            singleline_skipped=singleline_skipped,
            changed_files=changed_files,
        )

    def _is_filtered_name(self, name: str) -> bool:
        if not name:
            return True
        if name.startswith("_"):
            return True
        low = name.lower()
        if low.startswith("test_") or low.startswith("setup_") or low.startswith("teardown_"):
            return True
        return False

    def _iter_function_nodes(self, tree: ast.AST) -> List[ast.AST]:
        nodes: List[ast.AST] = []
        for node in getattr(tree, "body", []):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                nodes.append(node)
            elif isinstance(node, ast.ClassDef):
                for sub in getattr(node, "body", []):
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        nodes.append(sub)
        return nodes

    def _docstring_node(self, fn: ast.AST) -> Optional[ast.Expr]:
        if not hasattr(fn, "body"):
            return None
        body = getattr(fn, "body")
        if not body:
            return None
        first = body[0]
        if isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), ast.Constant) and isinstance(first.value.value, str):
            return first
        return None

    def _has_scope_tag(self, doc: Optional[str]) -> bool:
        if not doc:
            return False
        for line in doc.split("\n"):
            if line.strip().startswith("@harbor.scope:"):
                return True
        return False

    def _leading_whitespace(self, s: str) -> str:
        i = 0
        while i < len(s) and s[i] in (" ", "\t"):
            i += 1
        return s[:i]

    def _module_qual_from_path(self, p: Path) -> str:
        root = Path.cwd().resolve()
        try:
            rel = p.resolve().relative_to(root)
        except Exception:
            rel = p.name if p.is_file() else str(p)
            rel = Path(rel)
        parts = list(rel.parts)
        if parts and parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]
        return ".".join([x for x in parts if x and x not in (".", "..")])

    def _extract_functions(self, tree: ast.AST, module_qual: str) -> List[Tuple[str, str, int, int, Optional[str]]]:
        items: List[Tuple[str, str, int, int, Optional[str]]] = []
        for node in getattr(tree, "body", []):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name
                qual = f"{module_qual}.{name}"
                doc = ast.get_docstring(node)
                items.append((name, qual, getattr(node, "lineno", 0), getattr(node, "col_offset", 0), doc))
            elif isinstance(node, ast.ClassDef):
                for sub in getattr(node, "body", []):
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        name = sub.name
                        qual = f"{module_qual}.{node.name}.{name}"
                        doc = ast.get_docstring(sub)
                        items.append((name, qual, getattr(sub, "lineno", 0), getattr(sub, "col_offset", 0), doc))
        return items
