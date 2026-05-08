from types import SimpleNamespace

from harbor.core.contract_impact import (
    ContractImpactLevel,
    build_contract_impact_report,
    classify_contract_impact_for_file_path,
    classify_contract_impact_for_function_change,
    contract_impact_report_to_dict,
)


def test_cli_main_change_is_possible_with_cli_categories():
    finding = classify_contract_impact_for_function_change(
        func_id="harbor.cli.main.main",
        file_path="harbor/cli/main.py",
        change_type="Modified",
        details="Body + Contract changed",
    )
    values = [item.value for item in finding.categories]
    assert finding.level in (
        ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT,
        ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT,
    )
    assert "cli_args" in values
    assert "cli_text_output" in values


def test_to_dict_symbol_hits_cli_json_output():
    finding = classify_contract_impact_for_function_change(
        func_id="harbor.core.stale.stale_report_to_dict",
        file_path="harbor/core/stale.py",
        change_type="Modified",
        details="Body changed",
    )
    values = [item.value for item in finding.categories]
    assert finding.level == ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT
    assert "cli_json_output" in values


def test_write_function_hits_file_write_target_and_writes_files():
    finding = classify_contract_impact_for_function_change(
        func_id="harbor.core.diary.write_entry",
        file_path="harbor/core/diary.py",
    )
    values = [item.value for item in finding.categories]
    assert finding.level == ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT
    assert "file_write_target" in values
    assert "writes_files" in values


def test_generated_view_modules_hit_generated_view_format():
    level, categories, _ = classify_contract_impact_for_file_path("harbor/core/project_structure.py")
    values = [item.value for item in categories]
    assert level == ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT
    assert "generated_view_format" in values


def test_tests_helper_change_is_not_confirmed():
    level, _, _ = classify_contract_impact_for_file_path("tests/helpers/test_string_utils.py")
    assert level in (
        ContractImpactLevel.NO_CONTRACT_IMPACT,
        ContractImpactLevel.POSSIBLE_CONTRACT_IMPACT,
    )
    assert level != ContractImpactLevel.CONFIRMED_CONTRACT_IMPACT


def test_report_to_dict_is_deterministic_and_sanitized():
    records = [
        SimpleNamespace(
            id="harbor.core.diary.write_entry",
            file_path="C:/repo/harbor/core/diary.py",
            change_type="Modified",
            details="Body changed",
        ),
        SimpleNamespace(
            id="harbor.core.stale.stale_report_to_dict",
            file_path="C:/repo/harbor/core/stale.py",
            change_type="Modified",
            details="Body changed",
        ),
        SimpleNamespace(
            id="helper.fn",
            file_path="tests/helpers/test_utils.py",
            change_type="Drift",
            details="Body changed",
        ),
    ]
    report_1 = build_contract_impact_report(records)
    report_2 = build_contract_impact_report(list(reversed(records)))
    payload_1 = contract_impact_report_to_dict(report_1)
    payload_2 = contract_impact_report_to_dict(report_2)
    assert payload_1 == payload_2
    text = str(payload_1)
    assert "C:/" not in text
    assert "\\repo\\" not in text

