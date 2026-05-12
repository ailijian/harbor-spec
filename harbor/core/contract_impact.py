from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


class ContractImpactCategory(str, Enum):
    CLI_ARGS = "cli_args"
    CLI_TEXT_OUTPUT = "cli_text_output"
    CLI_JSON_OUTPUT = "cli_json_output"
    FILE_WRITE_TARGET = "file_write_target"
    WRITES_FILES = "writes_files"
    EXIT_CODE = "exit_code"
    PUBLIC_RETURNS = "public_returns"
    PUBLIC_RAISES = "public_raises"
    GENERATED_VIEW_FORMAT = "generated_view_format"
    CONFIG_SCHEMA = "config_schema"
    SAFETY_POLICY = "safety_policy"
    DDT_BINDING = "ddt_binding"
    SOURCE_OF_TRUTH_RULE = "source_of_truth_rule"


class ContractImpactLevel(str, Enum):
    NO_CONTRACT_IMPACT = "no_contract_impact"
    POSSIBLE_CONTRACT_IMPACT = "possible_contract_impact"
    CONFIRMED_CONTRACT_IMPACT = "confirmed_contract_impact"
    UNKNOWN = "unknown"


@dataclass
class ContractImpactFinding:
    level: ContractImpactLevel
    categories: List[ContractImpactCategory]
    func_id: str
    file_path: str
    reason: str
    evidence: str
    suggested_action: str
    confidence: str
    source: str


@dataclass
class ContractImpactReport:
    level: ContractImpactLevel
    categories: List[ContractImpactCategory]
    findings: List[ContractImpactFinding]
    summary_counts: Dict[str, int]
    notable_findings: List[ContractImpactFinding]


_WINDOWS_ABS_PATH_RE = re.compile(r"(?i)\b[a-z]:[\\/][^\s\"']+")
_POSIX_ABS_PATH_RE = re.compile(r"(?<![A-Za-z0-9_])/(?:[^ \t\r\n\"']+)")
_TO_DICT_RE = re.compile(r"(^|[_\.])(to_dict|report_to_dict|stale_report_to_dict)$", re.IGNORECASE)
_WRITE_FUNC_RE = re.compile(r"(^|[_\.])write[_a-z0-9]*$", re.IGNORECASE)
_DOCSTRING_RETURNS_RE = re.compile(r"\breturns?\b", re.IGNORECASE)
_DOCSTRING_RAISES_RE = re.compile(r"\braises?\b", re.IGNORECASE)
_TEST_PATH_RE = re.compile(r"(^|/)tests?/", re.IGNORECASE)


def classify_contract_impact_from_status_record(record: Any) -> ContractImpactFinding:
    return classify_contract_impact_for_function_change(
        func_id=str(getattr(record, "id", "") or ""),
        file_path=str(getattr(record, "file_path", "") or ""),
        change_type=str(getattr(record, "change_type", "") or ""),
        details=str(getattr(record, "details", "") or ""),
    )


def classify_contract_impact_for_function_change(
    *,
    func_id: str,
    file_path: str,
    change_type: str = "",
    details: str = "",
) -> ContractImpactFinding:
    file_level, file_categories, file_reason = classify_contract_impact_for_file_path(file_path=file_path)
    categories: Set[ContractImpactCategory] = set(file_categories)
    level = file_level

    normalized_path = _normalize_path(file_path).lower()
    in_test_path = _is_test_path(normalized_path)
    normalized_func = _normalize_symbol_for_classification(func_id).lower()
    details_lower = str(details or "").lower()
    change_type_lower = str(change_type or "").lower()

    if in_test_path:
        hit, test_categories, test_reason = _is_contract_asserting_test(
            func_id=normalized_func,
            file_path=normalized_path,
            evidence=f"{change_type_lower} {details_lower}",
        )
        categories.update(test_categories)
        if hit:
            level = _max_level(level, ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT)
            file_reason = test_reason
        else:
            level = ContractImpactLevel.NO_CONTRACT_IMPACT
            categories = set()
            file_reason = "tests path changed without explicit contract-test signal"
    else:
        if _is_to_dict_like(normalized_func):
            categories.add(ContractImpactCategory.CLI_JSON_OUTPUT)
            level = _max_level(level, ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT)

        if _is_write_like(normalized_func):
            categories.add(ContractImpactCategory.FILE_WRITE_TARGET)
            categories.add(ContractImpactCategory.WRITES_FILES)
            level = _max_level(level, ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT)

        if "argparse" in normalized_func or "parser" in normalized_func:
            categories.add(ContractImpactCategory.CLI_ARGS)
            level = _max_level(level, ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT)

        if "exit" in normalized_func:
            categories.add(ContractImpactCategory.EXIT_CODE)
            level = _max_level(level, ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT)

        if "format_" in normalized_func and "json" not in normalized_func:
            if "doctor" in normalized_func or "stale" in normalized_func or "report" in normalized_func:
                categories.add(ContractImpactCategory.CLI_TEXT_OUTPUT)
                level = _max_level(level, ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT)

    if "contract updated" in details_lower or "contract changed" in change_type_lower:
        # confirmed_contract_impact 表示确认 contract surface 变化，不表示 bug/breaking。
        level = _max_level(level, ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT)

    reason = file_reason or "status record classified by conservative heuristic"
    if normalized_func:
        reason = f"{reason}; symbol matched: {normalized_func}"
    if details_lower:
        reason = f"{reason}; details: {details_lower}"

    return ContractImpactFinding(
        level=level,
        categories=sorted(categories, key=lambda item: item.value),
        func_id=_sanitize_json_text(func_id),
        file_path=_sanitize_single_path(file_path),
        reason=reason,
        evidence=f"change_type={change_type or 'unknown'}",
        suggested_action="review contract surface and update tests/docs when behavior is intended",
        confidence=_confidence_for_level(level),
        source="status_record",
    )


def classify_contract_impact_for_file_path(file_path: str) -> Tuple[ContractImpactLevel, List[ContractImpactCategory], str]:
    rel = _normalize_path(file_path)
    rel_lower = rel.lower()
    categories: Set[ContractImpactCategory] = set()
    level = ContractImpactLevel.NO_CONTRACT_IMPACT
    reason = "no contract-impact pattern matched"

    if not rel_lower:
        return ContractImpactLevel.UNKNOWN, [], "empty file path"

    if _is_public_cli_path(rel_lower):
        categories.update({ContractImpactCategory.CLI_ARGS, ContractImpactCategory.CLI_TEXT_OUTPUT})
        level = _max_level(level, ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT)
        reason = "public CLI path changed"

    if _is_generated_view_module(rel_lower):
        categories.add(ContractImpactCategory.GENERATED_VIEW_FORMAT)
        level = _max_level(level, ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT)
        reason = "generated view formatter/generator path changed"

    if _is_docs_or_rules_path(rel_lower):
        categories.add(ContractImpactCategory.SOURCE_OF_TRUTH_RULE)
        level = _max_level(level, ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT)
        reason = "source-of-truth/rules/docs path changed"

    if rel_lower.endswith(".harbor/policy.yaml"):
        categories.add(ContractImpactCategory.CONFIG_SCHEMA)
        level = _max_level(level, ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT)
        reason = "policy schema path changed"
    if rel_lower.endswith(".harbor/safety.yaml"):
        categories.add(ContractImpactCategory.SAFETY_POLICY)
        level = _max_level(level, ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT)
        reason = "safety policy path changed"

    if _is_test_path(rel_lower):
        categories, level, reason = _classify_tests_path(rel_lower, categories, level)

    return level, sorted(categories, key=lambda item: item.value), reason


def classify_contract_impact_for_docstring_diff(
    *,
    func_id: str = "",
    file_path: str = "",
    diff_text: str = "",
    contract_updated: bool = False,
) -> ContractImpactFinding:
    categories: Set[ContractImpactCategory] = set()
    level = ContractImpactLevel.NO_CONTRACT_IMPACT
    diff_lower = str(diff_text or "").lower()

    if _DOCSTRING_RETURNS_RE.search(diff_lower):
        categories.add(ContractImpactCategory.PUBLIC_RETURNS)
        level = _max_level(level, ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT)
    if _DOCSTRING_RAISES_RE.search(diff_lower):
        categories.add(ContractImpactCategory.PUBLIC_RAISES)
        level = _max_level(level, ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT)
    if contract_updated and categories:
        # confirmed 仅表示 contract surface 变化已确认。
        level = _max_level(level, ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT)
    if not categories and diff_lower:
        level = ContractImpactLevel.UNKNOWN

    reason = "docstring diff analyzed for Returns/Raises contract surface"
    return ContractImpactFinding(
        level=level,
        categories=sorted(categories, key=lambda item: item.value),
        func_id=_sanitize_json_text(func_id),
        file_path=_sanitize_single_path(file_path),
        reason=reason,
        evidence=_sanitize_json_text(diff_text)[:280],
        suggested_action="confirm docstring contract and synchronize tests if public behavior changed",
        confidence=_confidence_for_level(level),
        source="docstring_diff",
    )


def build_contract_impact_report(records: Sequence[Any]) -> ContractImpactReport:
    findings = [classify_contract_impact_from_status_record(record) for record in records]
    findings = _sorted_findings(findings)

    counts = {
        ContractImpactLevel.NO_CONTRACT_IMPACT.value: 0,
        ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT.value: 0,
        ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT.value: 0,
        ContractImpactLevel.UNKNOWN.value: 0,
    }
    categories: Set[ContractImpactCategory] = set()
    overall_level = ContractImpactLevel.NO_CONTRACT_IMPACT
    for finding in findings:
        counts[finding.level.value] += 1
        categories.update(finding.categories)
        overall_level = _max_level(overall_level, finding.level)

    notable = [
        finding
        for finding in findings
        if finding.level in (ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT, ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT)
        and bool(finding.categories)
    ]
    return ContractImpactReport(
        level=overall_level,
        categories=sorted(categories, key=lambda item: item.value),
        findings=findings,
        summary_counts=counts,
        notable_findings=_sorted_findings(notable)[:5],
    )


def contract_impact_report_to_dict(report: ContractImpactReport) -> dict:
    """Serialize contract-impact analysis into stable JSON output.

    Behavior:
      - Preserves stable top-level keys for CLI/CI JSON consumers.
      - Sorts findings deterministically before serialization.
      - Sanitizes string fields so JSON output does not leak machine-local
        absolute paths.

    Args:
      report (ContractImpactReport): Contract-impact analysis result.

    Returns:
      dict: Stable JSON-compatible contract-impact payload.

    Side Effects:
      - Writes no files.

    Idempotency:
      - Deterministic for the same report state.

    Security:
      - Must not expose machine-local absolute paths in serialized findings.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: deterministic
    """
    normalized_findings = _sorted_findings(report.findings)
    normalized_notable = _sorted_findings(report.notable_findings)
    return {
        "level": report.level.value,
        "categories": [item.value for item in sorted(report.categories, key=lambda item: item.value)],
        "summary_counts": dict(report.summary_counts),
        "findings": [_finding_to_dict(item) for item in normalized_findings],
        "notable_findings": [_finding_to_dict(item) for item in normalized_notable],
        "advisory": True,
        "deterministic": True,
    }


def format_contract_impact_report(report: ContractImpactReport) -> str:
    counts = report.summary_counts
    lines = ["Contract Impact 分类："]
    lines.append(f"- {ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT.value}: {int(counts.get(ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT.value, 0))}")
    lines.append(f"- {ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT.value}: {int(counts.get(ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT.value, 0))}")
    lines.append(f"- {ContractImpactLevel.NO_CONTRACT_IMPACT.value}: {int(counts.get(ContractImpactLevel.NO_CONTRACT_IMPACT.value, 0))}")
    lines.append(f"- {ContractImpactLevel.UNKNOWN.value}: {int(counts.get(ContractImpactLevel.UNKNOWN.value, 0))}")

    if not report.notable_findings:
        lines.append("重点关注项：无")
        return "\n".join(lines)

    lines.append("重点关注项：")
    for finding in _sorted_findings(report.notable_findings):
        if not finding.categories:
            continue
        category = finding.categories[0].value
        target = finding.func_id or finding.file_path or "<unknown>"
        lines.append(f"- {category}: {target}")
    return "\n".join(lines)


def _finding_to_dict(finding: ContractImpactFinding) -> dict:
    return {
        "level": finding.level.value,
        "categories": [item.value for item in finding.categories],
        "func_id": _sanitize_json_text(finding.func_id),
        "file_path": _sanitize_single_path(finding.file_path),
        "reason": _sanitize_json_text(finding.reason),
        "evidence": _sanitize_json_text(finding.evidence),
        "suggested_action": _sanitize_json_text(finding.suggested_action),
        "confidence": finding.confidence,
        "source": finding.source,
    }


def _sorted_findings(items: Iterable[ContractImpactFinding]) -> List[ContractImpactFinding]:
    rank = {
        ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT: 0,
        ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT: 1,
        ContractImpactLevel.UNKNOWN: 2,
        ContractImpactLevel.NO_CONTRACT_IMPACT: 3,
    }
    return sorted(
        list(items),
        key=lambda item: (
            rank.get(item.level, 99),
            ",".join(category.value for category in item.categories),
            item.file_path,
            item.func_id,
        ),
    )


def _normalize_symbol(value: str) -> str:
    return _normalize_symbol_for_classification(value)


def _normalize_symbol_for_classification(value: str) -> str:
    return str(value or "").strip().replace("\\", "/")


def _normalize_path(value: str) -> str:
    if not value:
        return ""
    return _sanitize_single_path(str(value).strip())


def _max_level(left: ContractImpactLevel, right: ContractImpactLevel) -> ContractImpactLevel:
    rank = {
        ContractImpactLevel.NO_CONTRACT_IMPACT: 0,
        ContractImpactLevel.UNKNOWN: 1,
        ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT: 2,
        ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT: 3,
    }
    return left if rank.get(left, 0) >= rank.get(right, 0) else right


def _confidence_for_level(level: ContractImpactLevel) -> str:
    if level == ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT:
        return "high"
    if level == ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT:
        return "medium"
    if level == ContractImpactLevel.NO_CONTRACT_IMPACT:
        return "high"
    return "low"


def _is_public_cli_path(rel_lower: str) -> bool:
    if rel_lower.startswith("harbor/cli/"):
        return True
    return rel_lower == "harbor/cli/main.py"


def _is_generated_view_module(rel_lower: str) -> bool:
    return rel_lower in {
        "harbor/core/project_structure.py",
        "harbor/core/l2.py",
        "harbor/core/module_capsule.py",
        "harbor/core/context_integrity.py",
    }


def _is_docs_or_rules_path(rel_lower: str) -> bool:
    return (
        rel_lower == "agents.md"
        or rel_lower.startswith(".harbor/rules/")
        or rel_lower in {"readme.md", "readme.en.md", "release.md"}
        or rel_lower.startswith("docs/design/")
    )


def _classify_tests_path(
    rel_lower: str,
    categories: Set[ContractImpactCategory],
    level: ContractImpactLevel,
) -> Tuple[Set[ContractImpactCategory], ContractImpactLevel, str]:
    matched, test_categories, reason = _is_contract_asserting_test(
        func_id="",
        file_path=rel_lower,
        evidence="",
    )
    if matched:
        categories.update(test_categories)
        return categories, _max_level(level, ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT), reason
    return categories, ContractImpactLevel.NO_CONTRACT_IMPACT, "test-only helper change"


def _is_test_path(rel_lower: str) -> bool:
    if not rel_lower:
        return False
    return bool(_TEST_PATH_RE.search(rel_lower))


def _is_contract_asserting_test(
    *,
    func_id: str,
    file_path: str,
    evidence: str,
) -> Tuple[bool, Set[ContractImpactCategory], str]:
    haystack = " ".join([func_id or "", file_path or "", evidence or ""]).lower()
    categories: Set[ContractImpactCategory] = set()

    if "ddt" in haystack:
        categories.add(ContractImpactCategory.DDT_BINDING)
        return True, categories, "DDT binding test signal matched"

    generated_view_tokens = ("generated_view", "frontmatter")
    if any(token in haystack for token in generated_view_tokens):
        categories.add(ContractImpactCategory.GENERATED_VIEW_FORMAT)
        return True, categories, "generated view/frontmatter test signal matched"

    snapshot_tokens = ("snapshot", "golden")
    output_tokens = ("cli_output", "output_contract", "expected_output")
    json_output_tokens = ("json_output", "cli_json_output")
    contract_context_tokens = ("contract", "assert", "expected", "snapshot", "golden", "schema")

    has_snapshot = any(token in haystack for token in snapshot_tokens)
    has_output = any(token in haystack for token in output_tokens)
    has_json_output = any(token in haystack for token in json_output_tokens)
    if has_snapshot or has_output or (has_json_output and any(token in haystack for token in contract_context_tokens)):
        if has_json_output and any(token in haystack for token in contract_context_tokens):
            categories.add(ContractImpactCategory.CLI_JSON_OUTPUT)
            return True, categories, "CLI JSON output contract test signal matched"
        categories.add(ContractImpactCategory.CLI_TEXT_OUTPUT)
        return True, categories, "CLI text output contract test signal matched"

    if "write_target" in haystack:
        categories.add(ContractImpactCategory.FILE_WRITE_TARGET)
        return True, categories, "file write target contract test signal matched"

    if "exit_code" in haystack:
        categories.add(ContractImpactCategory.EXIT_CODE)
        return True, categories, "exit code contract test signal matched"

    schema_tokens = ("fixture_schema", "public_fixture", "schema")
    if any(token in haystack for token in schema_tokens):
        categories.add(ContractImpactCategory.SOURCE_OF_TRUTH_RULE)
        return True, categories, "schema/public fixture contract test signal matched"

    if "contract" in haystack:
        categories.add(ContractImpactCategory.SOURCE_OF_TRUTH_RULE)
        return True, categories, "explicit contract test signal matched"

    return False, categories, "no explicit contract-test signal matched"


def _is_to_dict_like(symbol: str) -> bool:
    if not symbol:
        return False
    leaf = symbol.split(".")[-1]
    if _TO_DICT_RE.search(leaf):
        return True
    return leaf.endswith("_to_dict") or "report_to_dict" in leaf


def _is_write_like(symbol: str) -> bool:
    if not symbol:
        return False
    leaf = symbol.split(".")[-1]
    if _WRITE_FUNC_RE.search(leaf):
        return True
    return leaf.startswith("write_")


def _sanitize_json_text(value: Optional[str]) -> str:
    if value is None:
        return ""

    def _replace(match: re.Match) -> str:
        return _sanitize_single_path(match.group(0))

    sanitized = _WINDOWS_ABS_PATH_RE.sub(_replace, value)
    sanitized = _POSIX_ABS_PATH_RE.sub(_replace, sanitized)
    return sanitized


def _sanitize_single_path(path_text: str) -> str:
    raw = str(path_text or "").strip()
    if not raw:
        return ""
    normalized = raw.replace("\\", "/")
    repo_root = Path.cwd().resolve()
    if re.match(r"(?i)^[a-z]:/", normalized) or normalized.startswith("//"):
        marker = f"/{repo_root.name.lower()}/"
        lower = normalized.lower()
        idx = lower.find(marker)
        if idx != -1:
            rel = normalized[idx + len(marker) :].strip("/")
            if rel:
                return rel
        base = Path(normalized.rstrip("/")).name or Path(normalized).name
        return base or normalized
    candidate = Path(normalized)
    if candidate.is_absolute():
        try:
            return candidate.resolve().relative_to(repo_root).as_posix()
        except Exception:
            return candidate.name or normalized
    return normalized
