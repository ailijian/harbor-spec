# Unreleased / v1.3.1 - Workspace Layout Migration (Phase 2A-2D-A)

## Changed
- Workspace config canonical write target is `.harbor/config/harbor.yaml`.
- Legacy `.harbor/config.yaml` remains readable for compatibility.
- `harbor project structure --write` now writes canonical `.harbor/views/project-structure.md` by default.
- `docs/harbor/project-structure.md` is now an optional export target, enabled only when:
  - `views.export.docs.enabled=true`
  - `views.export.docs.root` is configured (default `docs/harbor`)
- `harbor module seal --write` now writes canonical capsule files to `.harbor/views/modules/<module>/` by default.
- `docs/harbor/modules/<module>/` is now an optional docs export target for Module Capsule (disabled by default unless `views.export.docs.enabled=true`).
- `harbor module stale` now evaluates canonical capsule freshness from `.harbor/views/modules/<module>/module-card.md`.
- `harbor module promote-skill` now references canonical capsule paths under `.harbor/views/modules/<module>/...`.
- Doctor skill-reference check supports canonical capsule references and keeps legacy docs references as compatibility mode (non-canonical).
- `harbor docs --write` now writes canonical L2 README to `.harbor/views/l2/<module>/README.md`.
- `<module>/README.md` is now treated as an optional L2 export target (enabled by default via `l2.export.module_readme.enabled=true`).
- L2 metadata canonical write target is now `.harbor/views/l2/_meta.json`.
- Legacy `.harbor/l2_meta.json` remains read-compatible and is no longer a write target.
- Diary canonical write target is now `.harbor/diary/YYYY-MM.jsonl`.
- Legacy `specs/diary/YYYY-MM.jsonl` remains read-compatible and is no longer a write target.
- Diary reads merge canonical + legacy records with dedupe; no automatic migration/deletion is performed.
- `harbor stale` canonical freshness continues to be determined by `.harbor/views/l2/<module>/README.md` and is not affected by module README export drift.
- `harbor stale` now reports `l2_readme_export` advisory separately (`<module>/README.md`: match/missing/out-of-sync/disabled).
- If canonical L2 is unavailable, `l2_readme_export` is reported as unknown/skipped and out-of-sync comparison is skipped.
- `harbor doctor` Derived Views now include:
  - module README export advisory (`l2_readme_export`)
  - legacy metadata advisory when `.harbor/l2_meta.json` is detected
- Export mismatch and legacy metadata are advisory WARN signals (not FAIL), and no automatic cleanup/migration is performed.
- `harbor project structure` (without `--write`) remains preview-only and writes nothing.
- `.gitignore` no longer uses broad `.harbor/` ignore; Harbor tracking now uses subdirectory-level policies.
- Default tracked Harbor workspace assets include `.harbor/config/`, `.harbor/policy/`, `.harbor/views/project-structure.md`, `.harbor/diary/`, and selected `.harbor/reports/`.
- Default ignored Harbor runtime paths include `.harbor/state/`, `.harbor/cache/`, `.harbor/exports/`, `.harbor/reports/tmp/`, and `.harbor/reports/local/`.

## Compatibility
- Legacy `docs/harbor/project-structure.md` is not deleted or auto-migrated in this phase.
- Legacy `.harbor/l2_meta.json` is not deleted or auto-migrated in this phase.
- Legacy `specs/diary/*.jsonl` is not deleted or auto-migrated in this phase.
- Legacy `tests/fixtures_sqlite/README.md` is kept as a legacy L2 export artifact in this phase.
- Legacy `docs/harbor/modules/*` files are not deleted or auto-migrated in this phase.

## Migration Notes / 升级说明
- v1.3.1+ uses `.harbor/config/harbor.yaml` as the canonical config write target.
- Legacy `.harbor/config.yaml` is still readable for compatibility.
- Project Structure canonical path is `.harbor/views/project-structure.md`.
- `docs/harbor/project-structure.md` is an optional export target and is disabled by default.
- Module Capsule canonical path is `.harbor/views/modules/<module>/`.
- `docs/harbor/modules/<module>/` is an optional docs export target and is disabled by default.
- L2 README canonical path is `.harbor/views/l2/<module>/README.md`.
- L2 metadata canonical path is `.harbor/views/l2/_meta.json`.
- Diary canonical path is `.harbor/diary/YYYY-MM.jsonl`.
- `<module>/README.md` remains an optional export target for compatibility and stays enabled by default.
- Legacy `.harbor/l2_meta.json` remains read-compatible and is not auto-deleted.
- Legacy `specs/diary/YYYY-MM.jsonl` remains read-compatible and is not auto-deleted.
- `.harbor/` is the canonical Harbor workspace and should not be ignored as a whole in `.gitignore`.

---

# Unreleased / v1.3.0 - Workflow & Module Capsule Update

## Added
- Workflow facade commands:
  - `harbor start`
  - `harbor checkpoint`
  - `harbor finish --sync-context`
  - `harbor accept`
- L2 README refresh modes:
  - `harbor docs --changed`
  - `harbor docs --all`
- Module Capsule commands:
  - `harbor module inspect`
  - `harbor module seal`
  - `harbor module seal --changed`
  - `harbor module seal --all`
  - `harbor module stale`
  - `harbor module promote-skill`
- Top-level advisory checks:
  - `harbor stale`
  - `harbor doctor`
- Machine-readable JSON output for:
  - `harbor stale --format json`
  - `harbor doctor --format json`
- Project Structure View:
  - `harbor project structure`
  - `harbor project structure --write`

## Changed
- `module-card.md` now includes deterministic fingerprint frontmatter.
- `harbor finish` supports explicit context sync via `--sync-context`.
- CLI help and mutually-exclusive argument errors are clearer.
- README and README.en are aligned.
- Project Structure View now separates code modules from supporting areas and ranks key files for better AI context loading.

## Compatibility
- Existing `status`, `check`, `lock`, `docs --module`, and `log` behavior is preserved.
- Existing aliases are preserved.
- `harbor finish` default behavior remains non-writing.
- `harbor stale` and `harbor doctor` are advisory and read-only.
- Text output remains the default for `harbor stale` and `harbor doctor`.
- JSON output is advisory and does not change exit-code behavior.
- `harbor accept` is a semantic alias for `harbor lock`.
- Project Structure View is derived and does not replace Project Rules.
- `harbor project structure` is preview-only by default and does not write files.

## Runtime Safety
- No command automatically locks, logs, promotes skills, or writes context unless explicitly requested.
- Preview mode remains the default for docs and capsule generation where applicable.

## Release Validation

- Dogfooding completed across 8 RC scenarios.
- Mini RC Rerun completed after RC Fix Pack 1.
- `pytest` passed with 185 tests.
- Issue-001 / Issue-002 / Issue-003 verified fixed.
- No workspace-outside writes observed in the final rerun.
- `harbor stale` and `harbor doctor` text/json outputs verified.

## Migration Notes / 升级总览
- 本轮以发布收口为目标，重点是版本、文档、release notes 与命令帮助叙事对齐。
- 未新增任何 CLI 命令；现有命令行为语义保持不变。
- 升级后建议先执行 `harbor --help`、`harbor finish --help`、`harbor module --help` 验证入口与说明一致性。

---

# Harbor-spec v1.2.0 — The Industrial Update

## 🚀 Major Features
- Smart Configuration: `harbor init` 自动探测 Django、Node.js、Go、Java 技术栈并融合 `.gitignore` 规则
- SQLite Backend: 以 SQLite（WAL 模式）替代 JSON 索引，O(1) 内存占用、秒级启动与并发安全
- Parallel Indexing: `harbor lock` 利用多核 CPU 并行解析与哈希，显著提升构建吞吐

## ⚡ Performance
- 在超大仓库（100k+ 文件）中，将内存使用降低约 95%
- 通过增量数据库查询，将 `harbor status` 加速至原来的 100x

## 🛠 Improvements
- CLI 2.0：动词化命令集 —— `lock`、`check`、`log`、`adopt`；替换旧命令（`build-index` → `lock` 等）
- DDT Integration：`harbor check` 统一语义审计与测试绑定校验（`--fast` 仅 DDT）
- Windows Support：路径归一化与并行处理全面适配，跨平台稳定运行

## 🔧 Migration Notes
- 缓存索引路径：`.harbor/cache/harbor.db`（已在 `.gitignore` 中排除）
- 旧命令映射：`st` → `status`、`ddt validate` → `check --fast`、`diary export` → `log --export`、`decorate` → `adopt`、`gen l2` → `docs`

## 📦 Upgrade Checklist
- 运行 `harbor init` 以生成或更新配置（自动探测技术栈、合入 `.gitignore`）
- 运行 `harbor lock` 构建基线；随后使用 `harbor status` 验证变更检测速度
- 使用 `harbor check` 或 `harbor check --fast` 验证 DDT 绑定与语义一致性

## 📝 Acknowledgements
感谢所有贡献者在 Phase 12–16 中的努力，使 Harbor 在工业级规模下更加稳定与高效。
