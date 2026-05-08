from pathlib import Path

from harbor.core.context_integrity import (
    build_context_integrity_metadata,
    compute_source_fingerprint,
    content_without_generated_at_for_compare,
    merge_generated_at,
    parse_frontmatter,
    render_frontmatter,
    split_frontmatter,
)


def test_frontmatter_render_parse_roundtrip():
    metadata = {
        "generated_by": "harbor-spec",
        "harbor_version": "1.3.0",
        "view_type": "l2_readme",
        "module": "harbor/core",
        "generated_at": "2026-05-08T00:00:00Z",
        "generation_command": "harbor docs --module harbor/core --write",
        "stale_policy": "advisory",
        "source_path_count": 2,
        "source_paths_truncated": False,
        "source_paths": ["harbor/core/l2.py", "harbor/core/stale.py"],
        "source_fingerprint": "sha256:a",
        "contract_fingerprint": "sha256:b",
        "generator_fingerprint": "sha256:c",
    }
    markdown = render_frontmatter(metadata) + "\n\n# Body\n"
    parsed = parse_frontmatter(markdown)
    assert parsed is not None
    assert parsed["harbor_version"] == "1.3.0"
    assert parsed["view_type"] == "l2_readme"
    assert parsed["source_paths"] == ["harbor/core/l2.py", "harbor/core/stale.py"]


def test_content_without_generated_at_for_compare_ignores_only_timestamp():
    m1 = (
        '---\n'
        'generated_by: "harbor-spec"\n'
        'generated_at: "2026-05-08T00:00:00Z"\n'
        'source_fingerprint: "sha256:x"\n'
        'contract_fingerprint: "sha256:y"\n'
        'generator_fingerprint: "sha256:z"\n'
        '---\n\n'
        "# Body\n"
    )
    m2 = m1.replace("2026-05-08T00:00:00Z", "2026-05-09T00:00:00Z")
    assert content_without_generated_at_for_compare(m1) == content_without_generated_at_for_compare(m2)


def test_source_fingerprint_is_deterministic(tmp_path: Path):
    f1 = tmp_path / "harbor" / "core" / "a.py"
    f2 = tmp_path / "harbor" / "core" / "b.py"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("print('a')\n", encoding="utf-8")
    f2.write_text("print('b')\n", encoding="utf-8")

    p1 = compute_source_fingerprint(["harbor/core/b.py", "harbor/core/a.py"], repo_root=tmp_path)
    p2 = compute_source_fingerprint(["harbor/core/a.py", "harbor/core/b.py"], repo_root=tmp_path)
    assert p1 == p2
    assert p1.startswith("sha256:")


def test_metadata_has_no_absolute_paths(tmp_path: Path):
    f1 = tmp_path / "harbor" / "core" / "a.py"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("x=1\n", encoding="utf-8")
    metadata = build_context_integrity_metadata(
        view_type="module_card",
        module="harbor/core",
        generation_command="harbor module seal harbor/core --write",
        source_paths=[str(f1.resolve())],
        contract_records=[],
        repo_root=tmp_path,
    )
    assert metadata["source_paths"] == ["harbor/core/a.py"]
    assert ":" not in metadata["source_paths"][0]


def test_missing_file_handling_is_deterministic(tmp_path: Path):
    fp1 = compute_source_fingerprint(["harbor/core/missing.py"], repo_root=tmp_path)
    fp2 = compute_source_fingerprint(["harbor/core/missing.py"], repo_root=tmp_path)
    assert fp1 == fp2


def test_parser_rejects_complex_yaml():
    markdown = (
        "---\n"
        "source_paths:\n"
        "  - \"ok\"\n"
        "nested:\n"
        "  key: value\n"
        "---\n\n"
        "body\n"
    )
    parsed, _ = split_frontmatter(markdown)
    assert parsed is None


def test_merge_generated_at_keeps_old_when_fingerprints_and_body_same():
    previous = (
        "---\n"
        'source_fingerprint: "sha256:a"\n'
        'contract_fingerprint: "sha256:b"\n'
        'generator_fingerprint: "sha256:c"\n'
        'generated_at: "2026-05-08T00:00:00Z"\n'
        "---\n\n"
        "# body\n"
    )
    metadata = {
        "source_fingerprint": "sha256:a",
        "contract_fingerprint": "sha256:b",
        "generator_fingerprint": "sha256:c",
        "generated_at": "2026-05-09T00:00:00Z",
    }
    merged = merge_generated_at(previous, metadata, "# body\n")
    assert merged["generated_at"] == "2026-05-08T00:00:00Z"
