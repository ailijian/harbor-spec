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
