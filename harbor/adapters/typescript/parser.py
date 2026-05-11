from __future__ import annotations

import re
from typing import List, Optional, Tuple

from harbor.adapters.typescript.symbols import TypeScriptSymbol


_EXPORT_FUNCTION_RE = re.compile(r"export\s+(async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(")
_EXPORT_ARROW_RE = re.compile(r"export\s+const\s+([A-Za-z_$][\w$]*)\s*=\s*(async\s+)?\(")
_EXPORT_CLASS_RE = re.compile(r"export\s+class\s+([A-Za-z_$][\w$]*)\s*\{")
_PUBLIC_METHOD_RE = re.compile(r"(?m)^\s*public\s+(?:async\s+)?([A-Za-z_$][\w$]*)\s*\(")
_INTERNAL_FUNCTION_RE = re.compile(
    r"(?m)^\s*(?!export\b)(async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\("
)
_INTERNAL_ARROW_RE = re.compile(r"(?m)^\s*(?!export\b)const\s+([A-Za-z_$][\w$]*)\s*=\s*(async\s+)?\(")


def _to_lineno(source: str, offset: int) -> int:
    return source.count("\n", 0, offset) + 1


def _skip_ws(source: str, index: int) -> int:
    n = len(source)
    i = index
    while i < n and source[i].isspace():
        i += 1
    return i


def _find_matching(source: str, start: int, open_char: str, close_char: str) -> Optional[int]:
    if start >= len(source) or source[start] != open_char:
        return None
    depth = 0
    i = start
    n = len(source)
    in_single = False
    in_double = False
    in_backtick = False
    in_line_comment = False
    in_block_comment = False

    while i < n:
        ch = source[i]
        nxt = source[i + 1] if i + 1 < n else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
            i += 1
            continue
        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue

        if in_single:
            if ch == "\\":
                i += 2
                continue
            if ch == "'":
                in_single = False
            i += 1
            continue
        if in_double:
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                in_double = False
            i += 1
            continue
        if in_backtick:
            if ch == "\\":
                i += 2
                continue
            if ch == "`":
                in_backtick = False
            i += 1
            continue

        if ch == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue
        if ch == "'":
            in_single = True
            i += 1
            continue
        if ch == '"':
            in_double = True
            i += 1
            continue
        if ch == "`":
            in_backtick = True
            i += 1
            continue

        if ch == open_char:
            depth += 1
        elif ch == close_char:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def _extract_arrow_body(source: str, start_index: int) -> Tuple[Optional[str], int]:
    i = _skip_ws(source, start_index)
    if i >= len(source):
        return None, start_index
    if source[i] == "{":
        body_end = _find_matching(source, i, "{", "}")
        if body_end is None:
            return None, i
        return source[i : body_end + 1], body_end
    semi = source.find(";", i)
    end = semi if semi != -1 else len(source) - 1
    return source[i : end + 1].strip(), end


class TypeScriptLightweightParser:
    def __init__(self) -> None:
        self.diagnostics: List[str] = []

    def parse(self, source: str) -> List[TypeScriptSymbol]:
        symbols: List[TypeScriptSymbol] = []
        symbols.extend(self._parse_export_functions(source))
        symbols.extend(self._parse_export_arrow_functions(source))
        symbols.extend(self._parse_export_class_methods(source))
        symbols.extend(self._parse_internal_functions(source))
        symbols.extend(self._parse_internal_arrow_functions(source))
        symbols.sort(key=lambda item: (item.lineno, item.qualified_name))
        return symbols

    def _parse_export_functions(self, source: str) -> List[TypeScriptSymbol]:
        symbols: List[TypeScriptSymbol] = []
        for match in _EXPORT_FUNCTION_RE.finditer(source):
            async_kw = (match.group(1) or "").strip()
            name = match.group(2)
            paren_start = match.end() - 1
            paren_end = _find_matching(source, paren_start, "(", ")")
            if paren_end is None:
                self.diagnostics.append(f"skip export function `{name}`: unmatched parentheses")
                continue
            i = _skip_ws(source, paren_end + 1)
            while i < len(source) and source[i] != "{":
                i += 1
            if i >= len(source):
                self.diagnostics.append(f"skip export function `{name}`: missing body")
                continue
            body_end = _find_matching(source, i, "{", "}")
            if body_end is None:
                self.diagnostics.append(f"skip export function `{name}`: unmatched braces")
                continue
            signature_text = source[match.start() : i].strip()
            body_text = source[i : body_end + 1]
            symbols.append(
                TypeScriptSymbol(
                    name=name,
                    symbol_kind="function",
                    qualified_name=name,
                    export_kind="export_function_async" if async_kw else "export_function",
                    is_exported=True,
                    lineno=_to_lineno(source, match.start()),
                    end_lineno=_to_lineno(source, body_end),
                    signature_text=signature_text,
                    body_text=body_text,
                )
            )
        return symbols

    def _parse_export_arrow_functions(self, source: str) -> List[TypeScriptSymbol]:
        symbols: List[TypeScriptSymbol] = []
        for match in _EXPORT_ARROW_RE.finditer(source):
            name = match.group(1)
            async_kw = (match.group(2) or "").strip()
            paren_start = match.end() - 1
            paren_end = _find_matching(source, paren_start, "(", ")")
            if paren_end is None:
                self.diagnostics.append(f"skip export const `{name}`: unmatched parentheses")
                continue

            i = _skip_ws(source, paren_end + 1)
            if i < len(source) and source[i] == ":":
                i += 1
                while i < len(source):
                    if source[i] == "=" and i + 1 < len(source) and source[i + 1] == ">":
                        break
                    i += 1
            i = _skip_ws(source, i)
            if not (i + 1 < len(source) and source[i] == "=" and source[i + 1] == ">"):
                self.diagnostics.append(f"skip export const `{name}`: missing arrow")
                continue
            body_text, body_end = _extract_arrow_body(source, i + 2)
            if body_text is None:
                self.diagnostics.append(f"skip export const `{name}`: malformed body")
                continue
            signature_text = source[match.start() : i + 2].strip()
            symbols.append(
                TypeScriptSymbol(
                    name=name,
                    symbol_kind="function",
                    qualified_name=name,
                    export_kind="export_const_async_arrow" if async_kw else "export_const_arrow",
                    is_exported=True,
                    lineno=_to_lineno(source, match.start()),
                    end_lineno=_to_lineno(source, body_end),
                    signature_text=signature_text,
                    body_text=body_text,
                )
            )
        return symbols

    def _parse_export_class_methods(self, source: str) -> List[TypeScriptSymbol]:
        symbols: List[TypeScriptSymbol] = []
        for match in _EXPORT_CLASS_RE.finditer(source):
            class_name = match.group(1)
            body_start = match.end() - 1
            body_end = _find_matching(source, body_start, "{", "}")
            if body_end is None:
                self.diagnostics.append(f"skip export class `{class_name}`: unmatched braces")
                continue

            class_body = source[body_start + 1 : body_end]
            body_offset = body_start + 1
            for method_match in _PUBLIC_METHOD_RE.finditer(class_body):
                method_name = method_match.group(1)
                local_start = method_match.start()
                global_start = body_offset + local_start
                paren_start = body_offset + method_match.end() - 1
                paren_end = _find_matching(source, paren_start, "(", ")")
                if paren_end is None:
                    self.diagnostics.append(
                        f"skip method `{class_name}.{method_name}`: unmatched parentheses"
                    )
                    continue
                i = _skip_ws(source, paren_end + 1)
                while i < len(source) and source[i] != "{":
                    i += 1
                if i >= len(source):
                    self.diagnostics.append(f"skip method `{class_name}.{method_name}`: missing body")
                    continue
                method_body_end = _find_matching(source, i, "{", "}")
                if method_body_end is None:
                    self.diagnostics.append(
                        f"skip method `{class_name}.{method_name}`: unmatched braces"
                    )
                    continue
                if method_body_end > body_end:
                    self.diagnostics.append(
                        f"skip method `{class_name}.{method_name}`: method out of class body"
                    )
                    continue
                signature_text = source[global_start:i].strip()
                symbols.append(
                    TypeScriptSymbol(
                        name=method_name,
                        symbol_kind="method",
                        qualified_name=f"{class_name}.{method_name}",
                        export_kind="export_class_public_method",
                        is_exported=True,
                        lineno=_to_lineno(source, global_start),
                        end_lineno=_to_lineno(source, method_body_end),
                        signature_text=signature_text,
                        body_text=source[i : method_body_end + 1],
                        class_name=class_name,
                    )
                )
        return symbols

    def _parse_internal_functions(self, source: str) -> List[TypeScriptSymbol]:
        symbols: List[TypeScriptSymbol] = []
        for match in _INTERNAL_FUNCTION_RE.finditer(source):
            async_kw = (match.group(1) or "").strip()
            name = match.group(2)
            paren_start = match.end() - 1
            paren_end = _find_matching(source, paren_start, "(", ")")
            if paren_end is None:
                self.diagnostics.append(f"skip internal function `{name}`: unmatched parentheses")
                continue
            i = _skip_ws(source, paren_end + 1)
            while i < len(source) and source[i] != "{":
                i += 1
            if i >= len(source):
                self.diagnostics.append(f"skip internal function `{name}`: missing body")
                continue
            body_end = _find_matching(source, i, "{", "}")
            if body_end is None:
                self.diagnostics.append(f"skip internal function `{name}`: unmatched braces")
                continue
            symbols.append(
                TypeScriptSymbol(
                    name=name,
                    symbol_kind="function",
                    qualified_name=name,
                    export_kind="internal_function_async" if async_kw else "internal_function",
                    is_exported=False,
                    lineno=_to_lineno(source, match.start()),
                    end_lineno=_to_lineno(source, body_end),
                    signature_text=source[match.start() : i].strip(),
                    body_text=source[i : body_end + 1],
                    visibility="internal",
                )
            )
        return symbols

    def _parse_internal_arrow_functions(self, source: str) -> List[TypeScriptSymbol]:
        symbols: List[TypeScriptSymbol] = []
        for match in _INTERNAL_ARROW_RE.finditer(source):
            name = match.group(1)
            async_kw = (match.group(2) or "").strip()
            paren_start = match.end() - 1
            paren_end = _find_matching(source, paren_start, "(", ")")
            if paren_end is None:
                self.diagnostics.append(f"skip internal const `{name}`: unmatched parentheses")
                continue

            i = _skip_ws(source, paren_end + 1)
            if i < len(source) and source[i] == ":":
                i += 1
                while i < len(source):
                    if source[i] == "=" and i + 1 < len(source) and source[i + 1] == ">":
                        break
                    i += 1
            i = _skip_ws(source, i)
            if not (i + 1 < len(source) and source[i] == "=" and source[i + 1] == ">"):
                self.diagnostics.append(f"skip internal const `{name}`: missing arrow")
                continue
            body_text, body_end = _extract_arrow_body(source, i + 2)
            if body_text is None:
                self.diagnostics.append(f"skip internal const `{name}`: malformed body")
                continue

            symbols.append(
                TypeScriptSymbol(
                    name=name,
                    symbol_kind="function",
                    qualified_name=name,
                    export_kind="internal_const_async_arrow" if async_kw else "internal_const_arrow",
                    is_exported=False,
                    lineno=_to_lineno(source, match.start()),
                    end_lineno=_to_lineno(source, body_end),
                    signature_text=source[match.start() : i + 2].strip(),
                    body_text=body_text,
                    visibility="internal",
                )
            )
        return symbols
