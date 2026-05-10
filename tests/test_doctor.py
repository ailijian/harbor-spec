from pathlib import Path
from types import SimpleNamespace

import pytest

import harbor.core.doctor as doctor


@pytest.fixture(autouse=True)
def _force_en_locale(monkeypatch):
    monkeypatch.setenv("HARBOR_LANGUAGE", "en")


def _empty_status_report():
    return SimpleNamespace(
        counts={
            "drift": 0,
            "modified": 0,
            "contract_changed": 0,
            "contract_gap": 0,
            "skipped_no_contract": 0,
            "contract_parse_error": 0,
            "untracked": 0,
            "missing": 0,
        },
        drift=[],
        modified=[],
        contract_changed=[],
        contract_gap=[],
        skipped_no_contract=[],
        contract_parse_error=[],
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
        l2_readme_export=SimpleNamespace(
            status=status,
            reason=("module README export out of sync" if stale else "up to date"),
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
            l2_readme_export=SimpleNamespace(
                status="unknown",
                reason="canonical L2 README unavailable",
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


def test_derived_views_check_shows_disabled_without_counting_warn(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)

    def _disabled_summary(module):
        return SimpleNamespace(
            module=module,
            l2_readme=SimpleNamespace(status="up_to_date", reason="up to date", suggested_command=None),
            l2_readme_export=SimpleNamespace(
                status="disabled",
                reason="module README export disabled by config",
                suggested_command=None,
            ),
            module_capsule=SimpleNamespace(status="up_to_date", reason="up to date", suggested_command=None),
        )

    monkeypatch.setattr(doctor, "check_module_derived_views_stale", _disabled_summary)
    monkeypatch.setattr(Path, "exists", lambda self: False, raising=False)
    result = doctor.run_derived_views_check(["harbor/core"])
    assert result.status == doctor.PASS
    assert any("disabled:" in d and "module README export disabled by config" in d for d in result.details)


def test_derived_views_check_warns_for_legacy_metadata_but_never_fail(monkeypatch):
    monkeypatch.setattr(doctor, "check_module_derived_views_stale", lambda module: _sample_summary(module, stale=False))
    monkeypatch.setattr(
        Path,
        "exists",
        lambda self: True if self.as_posix().endswith(".harbor/l2_meta.json") else False,
        raising=False,
    )
    result = doctor.run_derived_views_check(["harbor/core"])
    assert result.status == doctor.WARN
    assert all("FAIL" not in d for d in result.details)
    assert any(".harbor/l2_meta.json" in d for d in result.details)


def test_derived_views_check_warns_for_legacy_diary_jsonl(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(doctor, "check_module_derived_views_stale", lambda module: _sample_summary(module, stale=False))
    legacy_dir = tmp_path / "specs" / "diary"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    (legacy_dir / "2026-05.jsonl").write_text('{"summary":"legacy"}\n', encoding="utf-8")
    result = doctor.run_derived_views_check(["harbor/core"])
    assert result.status == doctor.WARN
    assert any("workspace layout/project memory advisory" in d for d in result.details)
    assert any("specs/diary" in d for d in result.details)
    assert all("FAIL" not in d for d in result.details)


def test_derived_views_check_legacy_diary_empty_dir_no_warning(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(doctor, "check_module_derived_views_stale", lambda module: _sample_summary(module, stale=False))
    (tmp_path / "specs" / "diary").mkdir(parents=True, exist_ok=True)
    result = doctor.run_derived_views_check(["harbor/core"])
    assert result.status == doctor.PASS
    assert all("specs/diary" not in d for d in result.details)


def test_derived_views_check_legacy_diary_coexistence_single_advisory_and_no_mutation(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(doctor, "check_module_derived_views_stale", lambda module: _sample_summary(module, stale=False))
    canonical_dir = tmp_path / ".harbor" / "diary"
    canonical_dir.mkdir(parents=True, exist_ok=True)
    (canonical_dir / "2026-05.jsonl").write_text('{"summary":"canonical"}\n', encoding="utf-8")

    legacy_dir = tmp_path / "specs" / "diary"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    legacy_a = legacy_dir / "2026-05.jsonl"
    legacy_b = legacy_dir / "2026-06.jsonl"
    legacy_a.write_text('{"summary":"legacy-a"}\n', encoding="utf-8")
    legacy_b.write_text('{"summary":"legacy-b"}\n', encoding="utf-8")
    before_content = legacy_a.read_text(encoding="utf-8")
    before_mtime_ns = legacy_a.stat().st_mtime_ns

    result = doctor.run_derived_views_check(["harbor/core"])
    assert result.status == doctor.WARN
    assert sum(1 for d in result.details if "workspace layout/project memory advisory" in d) == 1
    assert any(".harbor/diary" in d for d in result.details)
    assert legacy_a.read_text(encoding="utf-8") == before_content
    assert legacy_a.stat().st_mtime_ns >= before_mtime_ns


def test_merge_status_never_downgrades_fail():
    assert doctor._merge_status(doctor.PASS, doctor.WARN) == doctor.WARN
    assert doctor._merge_status(doctor.WARN, doctor.WARN) == doctor.WARN
    assert doctor._merge_status(doctor.FAIL, doctor.WARN) == doctor.FAIL
    assert doctor._merge_status(doctor.FAIL, doctor.PASS) == doctor.FAIL


def test_skill_reference_check_skips_when_agents_skills_missing(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = doctor.run_skill_reference_check()
    assert result.status == doctor.SKIP


def test_skill_reference_check_warns_when_capsule_missing(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    skill = tmp_path / ".agents" / "skills" / "harbor-debug-harbor-core" / "SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text(
        "Read .harbor/views/modules/harbor/core/module-card.md first.",
        encoding="utf-8",
    )
    result = doctor.run_skill_reference_check()
    assert result.status == doctor.WARN
    assert any("missing capsule file" in d for d in result.details)
    assert "harbor module seal harbor/core --write" in result.suggestions


def test_skill_reference_check_passes_for_existing_canonical_reference(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    skill = tmp_path / ".agents" / "skills" / "harbor-debug-harbor-core" / "SKILL.md"
    card = tmp_path / ".harbor" / "views" / "modules" / "harbor" / "core" / "module-card.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    card.parent.mkdir(parents=True, exist_ok=True)
    card.write_text("ok\n", encoding="utf-8")
    skill.write_text("Read .harbor/views/modules/harbor/core/module-card.md first.", encoding="utf-8")
    result = doctor.run_skill_reference_check()
    assert result.status == doctor.PASS


def test_skill_reference_check_legacy_existing_warns_when_export_disabled(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    skill = tmp_path / ".agents" / "skills" / "harbor-debug-harbor-core" / "SKILL.md"
    legacy = tmp_path / "docs" / "harbor" / "modules" / "harbor" / "core" / "module-card.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text("ok\n", encoding="utf-8")
    skill.write_text("Read docs/harbor/modules/harbor/core/module-card.md first.", encoding="utf-8")
    result = doctor.run_skill_reference_check()
    assert result.status == doctor.WARN
    assert any("non-canonical" in d for d in result.details)


def test_skill_reference_check_legacy_existing_passes_when_export_enabled(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = tmp_path / ".harbor" / "config" / "harbor.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text("views:\n  export:\n    docs:\n      enabled: true\n      root: docs/harbor\n", encoding="utf-8")
    skill = tmp_path / ".agents" / "skills" / "harbor-debug-harbor-core" / "SKILL.md"
    legacy = tmp_path / "docs" / "harbor" / "modules" / "harbor" / "core" / "module-card.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text("ok\n", encoding="utf-8")
    skill.write_text("Read docs/harbor/modules/harbor/core/module-card.md first.", encoding="utf-8")
    result = doctor.run_skill_reference_check()
    assert result.status == doctor.PASS


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


def test_collect_next_steps_filters_high_impact_commands():
    checks = [
        doctor.DoctorCheckResult(
            "Workspace Status",
            doctor.WARN,
            ["changed"],
            ["harbor log", "harbor accept", "harbor lock", "harbor stale"],
        )
    ]
    steps = doctor._collect_next_steps(checks)
    assert all(not step.startswith("harbor log") for step in steps)
    assert all(not step.startswith("harbor accept") for step in steps)
    assert all(not step.startswith("harbor lock") for step in steps)
    assert "harbor stale" in steps


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


def test_derived_views_check_warns_when_frontmatter_missing(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    l2 = tmp_path / ".harbor" / "views" / "l2" / "harbor" / "core" / "README.md"
    card = tmp_path / ".harbor" / "views" / "modules" / "harbor" / "core" / "module-card.md"
    l2.parent.mkdir(parents=True, exist_ok=True)
    card.parent.mkdir(parents=True, exist_ok=True)
    l2.write_text("# plain body\n", encoding="utf-8")
    card.write_text("# plain body\n", encoding="utf-8")
    monkeypatch.setattr(doctor, "check_module_derived_views_stale", lambda module: _sample_summary(module, stale=False))
    result = doctor.run_derived_views_check(["harbor/core"])
    assert result.status == doctor.WARN
    assert any("frontmatter unknown" in d for d in result.details)
