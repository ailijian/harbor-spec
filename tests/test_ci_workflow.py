from pathlib import Path

import yaml


def test_ci_workflow_keeps_ubuntu_matrix_and_adds_windows_full_governance():
    workflow = Path(".github/workflows/ci.yml")
    payload = yaml.safe_load(workflow.read_text(encoding="utf-8"))

    jobs = payload["jobs"]
    ubuntu_job = jobs["build-test-audit"]
    windows_job = jobs["windows-full-governance"]

    assert ubuntu_job["runs-on"] == "ubuntu-latest"
    assert ubuntu_job["strategy"]["matrix"]["python-version"] == ["3.9", "3.10", "3.11"]

    assert windows_job["runs-on"] == "windows-latest"
    step_names = [step["name"] for step in windows_job["steps"]]
    assert step_names == [
        "Checkout",
        "Set up Python",
        "Upgrade pip",
        "Install package and tools",
        "Harbor verify-generated (CI gate)",
        "Run unit tests",
        "Harbor checkpoint (CI gate)",
        "Harbor stale (CI gate)",
        "Harbor doctor (CI gate)",
    ]
    assert windows_job["steps"][1]["with"]["python-version"] == "3.11"
    assert windows_job["steps"][4]["run"] == "harbor verify-generated --all --ci --format json"
    assert windows_job["steps"][5]["run"] == "pytest"
    assert windows_job["steps"][6]["run"] == "harbor checkpoint --ci --format json"
    assert windows_job["steps"][7]["run"] == "harbor stale --ci --format json"
    assert "--all" not in windows_job["steps"][7]["run"]
    assert windows_job["steps"][8]["run"] == "harbor doctor --ci --format json"
