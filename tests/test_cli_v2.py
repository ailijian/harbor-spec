import sys
from io import StringIO
from contextlib import redirect_stdout

from harbor.cli.main import main


def run_cmd(argv):
    buf = StringIO()
    with redirect_stdout(buf):
        sys.argv = ["harbor"] + argv
        main()
    return buf.getvalue()


def test_status_alias_st():
    out1 = run_cmd(["status"])
    out2 = run_cmd(["st"])
    assert "Harbor Context Status" in out1
    assert "Harbor Context Status" in out2
    assert out1.splitlines()[0] == out2.splitlines()[0]


def test_ddt_validate_maps_to_check_fast():
    out1 = run_cmd(["ddt", "validate"])
    out2 = run_cmd(["check", "--fast"])
    assert "Harbor Check Report:" in out1
    assert "Harbor Check Report:" in out2
    assert "[DDT] Validation:" in out1
    assert "[DDT] Validation:" in out2


def test_diary_export_maps_to_log_export():
    out1 = run_cmd(["diary", "export", "--visibility", "repo"])
    out2 = run_cmd(["log", "--export", "--visibility", "repo"])
    assert "# Harbor Diary Export" in out1
    assert "# Harbor Diary Export" in out2


def test_decorate_maps_to_adopt_dry_run():
    out1 = run_cmd(["adopt", "harbor", "--dry-run"])
    out2 = run_cmd(["decorate", "harbor", "--dry-run"])
    assert "Decorate Candidates" in out1
    assert "Decorate Candidates" in out2


def test_gen_l2_maps_to_docs():
    out1 = run_cmd(["gen", "l2", "--module", "harbor/core"])
    out2 = run_cmd(["docs", "--module", "harbor/core"])
    assert "# Module:" in out1
    assert "# Module:" in out2
