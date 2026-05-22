# Python Contract Source Recognition / Comparison Bugfix

## PR Title

`fix(python): recognize Harbor docstring sections and preserve contract-source metadata`

## Commit Message

`fix(python): repair contract source recognition and checkpoint comparison`

## Summary

This change fixes a Python contract-source recognition and comparison bug in Harbor v1.4.5.

The bug could incorrectly report `possible_semantic_drift` when a Python function body and docstring were both updated, as long as the updated docstring change lived mainly in Harbor-standard sections such as `Behavior:` rather than only in `Args:` / `Returns:` / `Raises:`.

The change also repairs Python contract-source metadata persistence so readonly index consumers and checkpoint full JSON can observe current contract-source fingerprints instead of losing them on Python paths.

## Root Cause

### 1. Python contract recognition was too narrow

Before this fix, Python docstring comparison only treated a small subset of sections as comparable contract text:

- `Args:`
- `Returns:`
- `Raises:`
- `@harbor.*`

Harbor-standard sections such as:

- `Behavior:`
- `Why:`
- `When:`
- `Invariants:`
- `Side Effects:`
- `Idempotency:`
- `Security:`
- CLI / output / file-write sections

were not included in the Python comparable contract area.

Result:

- AST could read the updated docstring correctly.
- The function target identity stayed correct.
- But `contract_hash` could remain unchanged when only these Harbor-standard sections changed.
- Checkpoint therefore compared `body_hash changed + contract_hash static` and emitted `possible_semantic_drift`.

### 2. Python contract-source explainability metadata was not preserved end-to-end

Python paths produced a `ContractSubject` with docstring contract source and fingerprint, but several persistence/read paths did not preserve that metadata consistently:

- Python index entries did not store the same additive `contract_source_*` metadata shape used by TypeScript.
- readonly DB fallback rebuilt Python items using a legacy subset of fields and dropped `contract_presence` / `contract_source_kinds` / `contract_source_fingerprints`.
- Python checkpoint status items therefore had weaker observability than TypeScript paths.

### 3. Contract-required detection was path-sensitive in the wrong way

Some Python indexing paths passed absolute file paths into `is_contract_required()`.

That could cause repo-rule checks like `harbor/cli/**` to fail matching during indexing, producing incorrect `contract_required=false` on paths that should have required contracts.

### 4. Legacy `None` vs `""` comparison could re-surface old gap noise

When comparing runtime DB items against current source items, `contract_hash=None` and `contract_hash=""` were not normalized consistently.

That could re-surface historical `contract_gap` noise on mtime-only changes.

## Fix Applied

### Python contract recognition

- Expanded Python comparable contract extraction to include Harbor-standard contract sections, not just `Args` / `Returns` / `Raises`.
- Expanded contract-like detection so `Behavior:`-only Harbor docstrings count as valid comparable contract sources when the target requires a contract.

### Persistence and readonly compatibility

- Persisted Python `contract_presence`, `contract_required`, `contract_source_kinds`, `contract_source_fingerprints`, and `source_confidence_summary` in the same additive style already used by TypeScript.
- Switched readonly DB fallback to reuse the canonical cache-item conversion path so Python metadata is not silently dropped.

### Checkpoint observability

- Propagated Python `contract_source_kinds` and `contract_source_fingerprints` into current snapshot items and status entries.
- This allows checkpoint full JSON to expose current Python contract-source fingerprints for investigation.

### Compatibility fix

- Normalized `None` / empty-string hash comparisons in the Python runtime comparison path.
- Normalized absolute paths to repo-relative form before contract-required checks.

## Compatibility Notes

- This does not relax checkpoint semantics.
- This does not downgrade `possible_semantic_drift` to advisory.
- This does not remove or weaken contract comparison.
- This preserves the existing rule that semantic drift only applies when a comparable contract exists.
- Existing accepted baselines still work; the fix only ensures Python contract changes are recognized more accurately and explained more clearly.
- readonly index consumers now receive richer Python metadata, additive to existing consumers.

## Regression Coverage

Added focused regression coverage for:

- Python function body + `Behavior:` docstring change should not become false `possible_semantic_drift`.
- Python contract fingerprint and contract-source fingerprint should both change when the docstring contract changes.
- checkpoint full JSON should expose Python `contract_source_kinds` and `contract_source_fingerprints`.
- readonly transient index should treat `Behavior:`-only required Python docstrings as `present`.
- readonly DB fallback should preserve Python contract-source metadata.

## Validation

### Targeted pytest

Ran:

```powershell
python -m pytest tests/test_python_contract_source_recognition.py tests/test_contract_presence.py tests/test_index_builder_registry_integration.py -q
```

Observed:

- pass

### Related pytest set

The user-provided PowerShell glob form did not expand directly, so the closest existing files were run explicitly:

```powershell
python -m pytest tests/test_checkpoint_ci.py tests/test_checkpoint_ci_baseline_artifact.py tests/test_checkpoint_ci_guidance.py tests/test_checkpoint_json_additive_compat.py tests/test_typescript_checkpoint_ci.py tests/test_ci_mode.py tests/test_l2_paths.py tests/test_module_capsule.py tests/test_module_capsule_stale.py tests/test_cli_module_capsule.py tests/test_cli_module_capsule_batch.py tests/test_cli_module_capsule_stale.py tests/test_module_skill.py tests/test_cli_module_skill.py tests/test_index_builder.py tests/test_index_builder_bad_syntax.py tests/test_index_builder_registry_integration.py tests/test_index_progress.py -q
```

Observed:

- pass

### Full pytest

Ran:

```powershell
python -m pytest
```

Observed:

- `763 passed`

### Harbor workflow

Ran:

```powershell
python -m harbor.cli.main checkpoint --ci --format json --detail summary
python -m harbor.cli.main finish --sync-context
python -m harbor.cli.main verify-generated --changed --ci --format json
python -m harbor.cli.main project structure --write
python -m harbor.cli.main docs --all --write
python -m harbor.cli.main module seal --all --write
python -m harbor.cli.main verify-generated --all --ci --format json
python -m harbor.cli.main stale --ci --format json
python -m harbor.cli.main doctor --ci --format json
```

Observed:

- `checkpoint --ci` still reports residuals and remains non-zero because the repository has intentional contract-change residuals that are not yet accepted.
- The three targets changed by this fix no longer report `possible_semantic_drift`; they now report `contract_and_body_changed`, which is the correct category.
- `verify-generated --all --ci --format json` passes after broader refresh.
- `stale --ci --format json` passes.
- `doctor --ci --format json` passes with one workspace warning about remaining change records.

## Minimal Changelog

### Fixed

- Fixed Python docstring contract recognition so Harbor-standard sections like `Behavior:` participate in comparable Python contract hashing.
- Fixed false `possible_semantic_drift` on Python targets whose implementation and docstring changed together.
- Fixed Python contract-source metadata persistence through index, readonly index, and checkpoint explainability paths.
- Fixed Python required-contract detection on absolute-path indexing paths.
- Fixed legacy `None` / empty-string contract hash comparison noise in runtime snapshot comparison.

### Tests

- Added regression tests for Python contract-source recognition, checkpoint JSON observability, and readonly index compatibility.

### Compatibility

- Additive change only for readonly/checkpoint metadata exposure.
- No weakening of semantic drift policy.
- No baseline acceptance performed.

## Reviewer Focus

- Confirm Harbor-standard Python docstring sections should be part of comparable contract text.
- Confirm additive Python `contract_source_*` metadata does not break existing consumers.
- Confirm checkpoint classification changed from false `possible_semantic_drift` to correct `contract_and_body_changed` for intentional contract/body edits.

## Not Done

- No version bump.
- No `RELEASE.md` change.
- No `harbor accept`.
- No diary write.
- No release or tag operation.
