from pathlib import Path
from types import SimpleNamespace

import pytest

import harbor.core.doctor as doctor


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


def _empty_status_report():
    return SimpleNamespace(
        counts={"drift": 0, "modified": 0, "contract_changed": 0, "untracked": 0, "missing": 0},
        drift=[],
        modified=[],
        contract_changed=[],
        untracked=[],
        missing=[],
    )


def _sample_summary(module: str, stale: bool):
    status = "stale" if stale else "up_to_date"
    reason = "README content mismatch" if stale else "up to date"
    return SimpleNamespace(
        module=module,
        l2_readme=SimpleNamespace(
            status=status,
            reason=reason,
            suggested_command=(f"harbor docs --module {module} --write" if stale else None),
        ),
        module_capsule=SimpleNamespace(
            status=status,
            reason=reason,
            suggested_command=(f"harbor module seal {module} --write" if stale else None),
        ),
    )


def test_doctor_report_formats_pass_warn_fail_skip():
    report = doctor.DoctorReport(
        scope="changed modules",
        checks=[
            doctor.DoctorCheckResult("Config / Index", doctor.PASS, ["ok"], []),
            doctor.DoctorCheckResult("Workspace Status", doctor.WARN, ["warn"], ["harbor finish"]),
            doctor.DoctorCheckResult("DDT Fast Check", doctor.FAIL, ["failed"], []),
            doctor.DoctorCheckResult("Skill References", doctor.SKIP, ["skip"], []),
        ],
    )
    out = doctor.format_doctor_report(report)
    assert "Harbor Doctor" in out
    assert "Config / Index: PASS" in out
    assert "Workspace Status: WARN" in out
    assert "DDT Fast Check: FAIL" in out
    assert "Skill References: SKIP" in out


def test_derived_views_check_reuses_stale_results(monkeypatch):
    called = []

    def _fake_check(module):
        called.append(module)
        return _sample_summary(module, stale=True)

    monkeypatch.setattr(doctor, "check_module_derived_views_stale", _fake_check)
    result = doctor.run_derived_views_check(["harbor/core", "harbor/cli"])
    assert called == ["harbor/core", "harbor/cli"]
    assert result.status == doctor.WARN
    assert any("harbor docs --module harbor/core --write" in s for s in result.suggestions)


def test_derived_views_check_marks_unknown_detail_as_unknown_not_stale(monkeypatch):
    def _unknown_summary(module):
        return SimpleNamespace(
            module=module,
            l2_readme=SimpleNamespace(
                status="unknown",
                reason="no indexed records found for module",
                suggested_command=None,
            ),
            module_capsule=SimpleNamespace(
                status="unknown",
                reason="no indexed records found for module",
                suggested_command=None,
            ),
        )

    monkeypatch.setattr(doctor, "check_module_derived_views_stale", _unknown_summary)
    result = doctor.run_derived_views_check(["tests/fixtures_sqlite"])
    assert result.status == doctor.WARN
    assert any("unknown: no indexed records found for module" in d for d in result.details)
    assert all("stale: no indexed records found for module" not in d for d in result.details)


def test_skill_reference_check_skips_when_agents_skills_missing(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = doctor.run_skill_reference_check()
    assert result.status == doctor.SKIP


def test_skill_reference_check_warns_when_capsule_missing(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    skill = tmp_path / ".agents" / "skills" / "harbor-debug-harbor-core" / "SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text(
        "Read docs/harbor/modules/harbor/core/module-card.md first.",
        encoding="utf-8",
    )
    result = doctor.run_skill_reference_check()
    assert result.status == doctor.WARN
    assert any("missing capsule file" in d for d in result.details)
    assert "harbor module seal harbor/core --write" in result.suggestions


def test_doctor_report_includes_suggestions():
    report = doctor.DoctorReport(
        scope="changed modules",
        checks=[
            doctor.DoctorCheckResult(
                "Derived Views",
                doctor.WARN,
                ["harbor/core stale"],
                ["harbor docs --module harbor/core --write"],
            )
        ],
    )
    out = doctor.format_doctor_report(report)
    assert "Suggested next steps:" in out
    assert "harbor docs --module harbor/core --write" in out


def test_build_doctor_report_is_read_only(monkeypatch):
    monkeypatch.setattr(doctor, "run_config_index_check", lambda: doctor.DoctorCheckResult("a", doctor.PASS, [], []))
    monkeypatch.setattr(doctor, "run_workspace_status_check", lambda sync_engine=None: doctor.DoctorCheckResult("b", doctor.PASS, [], []))
    monkeypatch.setattr(doctor, "run_ddt_fast_check", lambda scanner=None, validator=None: doctor.DoctorCheckResult("c", doctor.PASS, [], []))
    monkeypatch.setattr(doctor, "run_derived_views_check", lambda modules: doctor.DoctorCheckResult("d", doctor.PASS, [], []))
    monkeypatch.setattr(doctor, "run_skill_reference_check", lambda skills_root=Path(".agents") / "skills": doctor.DoctorCheckResult("e", doctor.SKIP, [], []))

    def _write_forbidden(*args, **kwargs):
        raise AssertionError("write_text must not be called")

    monkeypatch.setattr(Path, "write_text", _write_forbidden, raising=False)
    report = doctor.build_doctor_report(scope="changed modules", modules=["harbor/core"])
    assert len(report.checks) == 5
