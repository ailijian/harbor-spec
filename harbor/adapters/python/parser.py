from __future__ import annotations

import ast
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Union, Literal


@dataclass
class FunctionContract:
    id: str
    name: str
    qualified_name: str
    signature_hash: str
    docstring: Optional[str]
    docstring_raw_hash: Optional[str]
    contract_hash: Optional[str]
    lineno: int
    col_offset: int
    scope: Optional[Literal["public", "internal"]] = None
    strictness: Optional[Literal["strict", "standard", "light"]] = None
    is_method: bool = False
    parent_class: Optional[str] = None


class PythonAdapter:
    def parse_file(self, file_path: str) -> List[FunctionContract]:
        """解析并提取指定 Python 文件中的函数/方法契约元数据。

        功能:
          - 读取并解析 Python 源文件的 AST。
          - 提取所有顶层函数与类方法的名称、签名哈希与 Docstring 双哈希。
          - 识别 Docstring 中的 `@harbor.*` 标签与契约区 (Args/Returns/Raises) 文本。

        使用场景:
          - Harbor 索引构建（Phase 1）基座；为 `build-index` 提供 L3 解析能力。
          - `harbor sync l3 --check` 的前置分析。

        依赖:
          - Python 标准库 `ast`、`hashlib`。

        @harbor.scope: public
        @harbor.l3_strictness: strict
        @harbor.idempotency: read-only

        Args:
          file_path (str): 需要解析的 Python 源文件路径。

        Returns:
          List[FunctionContract]: 函数/方法契约元数据列表。

        Raises:
          IOError: 当文件读取失败。
          SyntaxError: 当源文件存在语法错误，无法解析为 AST。
        """
        p = Path(file_path)
        if not p.exists():
            raise IOError(f"file not found: {file_path}")
        try:
            source = p.read_text(encoding="utf-8")
        except Exception as e:
            raise IOError(str(e))
        try:
            tree = ast.parse(source)
        except SyntaxError:
            raise
        module_qual = self._module_qual_from_path(p)
        return self._extract_functions(tree, module_qual)

    def _extract_functions(self, tree: ast.AST, module_qual: str) -> List[FunctionContract]:
        """提取顶层函数与类方法的契约元数据。

        @harbor.scope: internal
        @harbor.l3_strictness: standard

        Args:
          tree (ast.AST): 已解析的抽象语法树。
          module_qual (str): 模块的点分限定名。

        Returns:
          List[FunctionContract]: 契约元数据列表。
        """
        items: List[FunctionContract] = []
        for node in getattr(tree, "body", []):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                items.append(self._contract_from_function(node, module_qual, None))
            elif isinstance(node, ast.ClassDef):
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        items.append(self._contract_from_function(sub, module_qual, node.name))
        return items

    def _contract_from_function(
        self,
        fn: Union[ast.FunctionDef, ast.AsyncFunctionDef],
        module_qual: str,
        parent_class: Optional[str],
    ) -> FunctionContract:
        """根据函数节点生成契约元数据。

        @harbor.scope: internal
        @harbor.l3_strictness: standard

        Args:
          fn: 函数或方法的 AST 节点。
          module_qual: 模块限定名。
          parent_class: 若为方法，则为父类名，否则为 None。

        Returns:
          FunctionContract: 契约元数据。
        """
        name = fn.name
        is_method = parent_class is not None
        qualified_name = (
            f"{module_qual}.{parent_class}.{name}" if is_method else f"{module_qual}.{name}"
        )
        doc = ast.get_docstring(fn)
        raw_hash, contract_hash = self._docstring_hashes(doc)
        scope, strictness = self._parse_tags(doc) if doc else (None, None)
        return FunctionContract(
            id=qualified_name,
            name=name,
            qualified_name=qualified_name,
            signature_hash=self._signature_hash(fn),
            docstring=doc,
            docstring_raw_hash=raw_hash,
            contract_hash=contract_hash,
            lineno=getattr(fn, "lineno", 0),
            col_offset=getattr(fn, "col_offset", 0),
            scope=scope,
            strictness=strictness,
            is_method=is_method,
            parent_class=parent_class,
        )

    def _signature_hash(self, fn: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> str:
        """计算函数签名的稳定哈希。

        @harbor.scope: internal
        @harbor.l3_strictness: standard

        Args:
          fn: 函数或方法的 AST 节点。

        Returns:
          str: 签名的 sha256 哈希。
        """
        a = fn.args
        parts = [
            "posonly:" + ",".join([x.arg for x in getattr(a, "posonlyargs", [])]),
            "args:" + ",".join([x.arg for x in a.args]),
            "vararg:" + (a.vararg.arg if a.vararg else ""),
            "kwonly:" + ",".join([x.arg for x in a.kwonlyargs]),
            "kwarg:" + (a.kwarg.arg if a.kwarg else ""),
            "defaults:" + str(len(a.defaults)) + "|" + str(len(a.kw_defaults)),
        ]
        norm = "|".join(parts)
        return hashlib.sha256(norm.encode("utf-8")).hexdigest()

    def _docstring_hashes(self, doc: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """计算 Docstring 的 raw/contract 双哈希。

        @harbor.scope: internal
        @harbor.l3_strictness: standard

        Args:
          doc: Docstring 文本或 None。

        Returns:
          Tuple[str | None, str | None]: (raw_hash, contract_hash)。
        """
        if not doc:
            return None, None
        text = doc.replace("\r\n", "\n").strip()
        raw = hashlib.sha256(text.encode("utf-8")).hexdigest()
        contract_text = self._contract_area(text)
        if not contract_text:
            return raw, raw
        contract = hashlib.sha256(contract_text.encode("utf-8")).hexdigest()
        return raw, contract

    def _contract_area(self, doc: str) -> str:
        """提取契约区文本（Args/Returns/Raises + @harbor.* tags）。找不到则返回空串。

        @harbor.scope: internal
        @harbor.l3_strictness: standard

        Args:
          doc: 完整 Docstring。

        Returns:
          str: 契约区文本。
        """
        lines = doc.split("\n")
        captured: List[str] = []
        capturing = False
        target_headers = {"Args:", "Returns:", "Raises:"}
        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("@harbor."):
                captured.append(s)
                continue
            if s in target_headers:
                capturing = True
                captured.append(s)
                continue
            if capturing:
                if s == "":
                    capturing = False
                    continue
                if line.startswith(" ") or line.startswith("\t"):
                    captured.append(line.rstrip())
                else:
                    capturing = False
        return "\n".join([x for x in captured if x.strip()]).strip()

    def _parse_tags(
        self, doc: str
    ) -> Tuple[Optional[Literal["public", "internal"]], Optional[Literal["strict", "standard", "light"]]]:
        """从 Docstring 提取 @harbor.* 标签。

        @harbor.scope: internal
        @harbor.l3_strictness: standard

        Args:
          doc: 完整 Docstring。

        Returns:
          Tuple[scope, strictness]: 若未找到则返回 (None, None)。
        """
        scope: Optional[Literal["public", "internal"]] = None
        strictness: Optional[Literal["strict", "standard", "light"]] = None
        for line in doc.split("\n"):
            s = line.strip()
            if s.startswith("@harbor.scope:"):
                val = s.split(":", 1)[1].strip()
                if val in ("public", "internal"):
                    scope = val  # type: ignore
            elif s.startswith("@harbor.l3_strictness:"):
                val = s.split(":", 1)[1].strip()
                if val in ("strict", "standard", "light"):
                    strictness = val  # type: ignore
        return scope, strictness

    def _module_qual_from_path(self, p: Path) -> str:
        """根据文件路径生成模块限定名（点分格式）。

        @harbor.scope: internal
        @harbor.l3_strictness: standard

        Args:
          p: 源文件路径。

        Returns:
          str: 点分模块名，如 `harbor.adapters.python.parser`。
        """
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

