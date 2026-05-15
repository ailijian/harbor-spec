# Harbor-spec Runtime Performance Baseline Report

- Generated at: `2026-05-15T15:00:13Z`
- Scope: `Task Group D / v1.4.5 runtime baseline on harbor-spec repository`
- Repo root: `E:/project/harbor-spec`
- Python: `3.11.5`
- Platform: `Windows-10-10.0.26200-SP0`

## Command Matrix

- `checkpoint` | scenario=`interactive text / repo-owned clean workspace` | status=`executed`
  - phase-style progress forced through TTY stderr capture
- `checkpoint --ci --format json --detail summary` | scenario=`machine JSON / repo-owned clean workspace` | status=`executed`
  - accepted baseline artifact path
- `finish` | scenario=`interactive text / repo-owned clean workspace` | status=`executed`
  - includes change-window runtime state write
- `check` | scenario=`interactive text / repo-owned clean workspace` | status=`executed`
  - full semantic path with preview disabled by default
- `verify-generated --all --ci --format json` | scenario=`machine JSON / repo-owned clean workspace` | status=`executed`
  - all-scope generated verification path
- `stale --all --ci --format json` | scenario=`machine JSON / repo-owned clean workspace` | status=`executed`
  - all-scope stale verification path
- `doctor --all --ci --format json` | scenario=`machine JSON / repo-owned clean workspace` | status=`executed`
  - all-scope doctor report path
- `docs --all --write` | scenario=`interactive text / scratch copy` | status=`executed`
  - write-path measured on temporary scratch copy to avoid mutating working tree
- `module seal --all --write` | scenario=`interactive text / scratch copy` | status=`executed`
  - write-path measured on temporary scratch copy to avoid mutating working tree
- `accept` | scenario=`repo-owned workspace` | status=`policy_gated`
  - not executed because Harbor policy requires an explicit user request for harbor accept

## Observations

| Command | Scenario | Format | Progress | Wall(s) | CPU(s) | Exit | Files | Targets | Modules | DDT | Preview Bindings | Preview Audit Targets | Cache | Incremental |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| checkpoint | interactive text / repo-owned clean workspace | text | yes | 1.375 | 1.297 | 0 | 174 | 1800 | 10 | 5 | 0 | n/a | runtime_cache_snapshot | n/a |
- Note `checkpoint`: progress-enabled text path
| checkpoint | machine JSON / repo-owned clean workspace | json | no | 7.987 | 7.859 | 1 | 174 | 1800 | 10 | 5 | 0 | n/a | accepted_artifact | n/a |
- Note `checkpoint`: summary CI path
| finish | interactive text / repo-owned clean workspace | text | yes | 26.007 | 1.922 | 0 | 174 | 1800 | 10 | 5 | 0 | n/a | runtime_cache_snapshot | n/a |
- Note `finish`: post-optimization run reuses status report inside finish
| check | interactive text / repo-owned clean workspace | text | yes | 11.403 | 1.922 | 0 | 174 | 1800 | 10 | 5 | 0 | n/a | runtime_cache_snapshot | n/a |
- Note `check`: full DDT plus semantic target collection path
| verify-generated | machine JSON / repo-owned clean workspace | json | no | 23.783 | 23.453 | 1 | 174 | 1800 | 10 | 5 | 0 | n/a | fresh_source_preferred | all_scope_full |
- Note `verify-generated`: all modules
| stale | machine JSON / repo-owned clean workspace | json | no | 16.040 | 15.906 | 1 | 174 | 1800 | 10 | 5 | 0 | n/a | fresh_source_preferred | all_scope_full |
- Note `stale`: all modules
| doctor | machine JSON / repo-owned clean workspace | json | no | 17.364 | 17.203 | 0 | 174 | 1800 | 10 | 5 | 0 | n/a | fresh_source_preferred | all_scope_full |
- Note `doctor`: all modules
| docs | interactive text / scratch copy | text | yes | 26.117 | 25.641 | 0 | 174 | 1800 | 10 | 5 | 0 | n/a | fresh_source_preferred | all_scope_full |
- Note `docs`: scratch copy
| module seal | interactive text / scratch copy | text | yes | 0.605 | 0.594 | 0 | 174 | 1800 | 10 | 5 | 0 | n/a | fresh_source_preferred | all_scope_full |
- Note `module seal`: scratch copy

## Hotspots

- `finish duplicate status scan`
  - Evidence: finish now runs at wall=26.007s after reusing the initial status report; previous implementation called SyncEngine.check_status() twice in the same workflow.
  - Recommendation: Keep the reuse in v1.4.5 as the only quick win and defer broader finish pipeline restructuring.
  - Quick win: yes
- `generated context all-scope write paths`
  - Evidence: docs --all --write wall=26.117s and module seal --all --write wall=0.605s dominate the measured all-scope write workflows.
  - Recommendation: Use these paths as the primary candidates if v1.4.6 becomes a dedicated performance release.
  - Quick win: no
- `generated verification all-scope scan`
  - Evidence: verify-generated --all --ci --format json completed in wall=23.783s and shares the same source-derived readonly-index path as stale/doctor.
  - Recommendation: If future regressions appear, profile repeated module-context and readonly-index construction first.
  - Quick win: no
- `checkpoint stage mix`
  - Evidence: checkpoint --ci --format json --detail summary completed in wall=7.987s; stage-level timing is still inferred from code structure rather than explicit per-stage timers.
  - Recommendation: Do not add new public timing output in v1.4.5; add internal profiling only if v1.4.6 is approved.
  - Quick win: no

## Quick Wins

- Implemented the low-risk finish optimization by reusing the first status report during full check execution.

## Deferred Structural Optimizations

- Do not introduce a new public performance/profiling CLI surface in v1.4.5.
- Do not start structural cache redesign, concurrency changes, or provider-level semantic-audit tuning in v1.4.5.
- Keep accept in the frozen matrix but leave execution to an explicit user-authorized follow-up.

## Recommendation

- The baseline now exists and the obvious quick win is closed. v1.4.6 should become a dedicated performance release only if generated-context all-scope write paths or repeated readonly-index work show materially worse latency in broader repositories than this harbor-spec baseline.
