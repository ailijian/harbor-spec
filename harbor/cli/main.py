import argparse
import os
from datetime import datetime, timezone
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TextColumn, BarColumn, MofNCompleteColumn, TimeElapsedColumn
import json
from rich.panel import Panel
from rich.prompt import Prompt

from harbor.utils.i18n import t, get_lang

from harbor.core.index import IndexBuilder
from harbor.core.sync import SyncEngine
from harbor.core.ddt import DDTScanner, DDTValidator
from harbor.core.changed_scope import (
    collect_changed_modules_from_status,
    collect_changed_paths_from_status,
    detect_generator_integrity_changes,
)
from harbor.core.l2 import L2Generator, collect_all_indexed_modules
from harbor.core.module_capsule import (
    check_module_capsule_stale,
    collect_module_context,
    preview_module_capsule,
    resolve_module_capsule_paths,
    write_module_capsule,
)
from harbor.core.module_skill import (
    check_capsule_ready_for_skill,
    write_module_skill,
)
from harbor.core.project_structure import (
    collect_project_structure_context,
    generate_project_structure_markdown,
    write_project_structure,
)
from harbor.core.stale import (
    check_module_derived_views_stale,
    format_stale_summary,
    stale_report_to_dict,
)
from harbor.core.generated_verify import (
    build_generated_verification_ci_result,
    build_generated_verification_report,
    format_generated_verification_report,
    generated_verification_report_to_dict,
)
from harbor.core.doctor import (
    build_doctor_report,
    format_doctor_report,
)
from harbor.core.ci import (
    build_doctor_ci_result,
    build_checkpoint_ci_result,
    build_stale_ci_result,
    ci_result_to_dict,
    checkpoint_ci_result_to_dict,
    format_checkpoint_ci_result,
    format_ci_result,
)
from harbor.core.baseline_artifact import (
    ACCEPTED_CHECKPOINT_BASELINE_PATH,
    AcceptedBaselineInvalidError,
    AcceptedBaselineMissingError,
    build_checkpoint_baseline_artifact,
    load_checkpoint_baseline_artifact,
    write_checkpoint_baseline_artifact,
)
from harbor.core.advice_config import resolve_advice_settings
from harbor.core.repair_guidance import (
    generic_conservative_guidance,
    guidance_for_checkpoint_category,
    guidance_for_doctor_item,
    guidance_for_stale_item,
)
from harbor.core.workspace_inspect import (
    build_workspace_inspect_report,
    format_workspace_inspect_report,
    workspace_inspect_report_to_dict,
)
from harbor.core.workspace_migrate import (
    build_workspace_migrate_dry_run_report,
    format_workspace_migrate_report,
    workspace_migrate_report_to_dict,
)
from harbor.core.contract_impact import (
    build_contract_impact_report,
    format_contract_impact_report,
)
from harbor.core.change_window import write_change_window_snapshot
from harbor.core.log_draft import (
    LogDraftError,
    build_log_write_preview,
    build_saved_diary_draft_output_path,
    build_diary_draft,
    serialize_diary_draft,
    write_diary_entry_from_draft,
    write_latest_diary_draft_cache,
    write_diary_draft_output,
)
from harbor.core.diary import DiaryManager
from harbor.core.audit import SemanticGuard, resolve_provider
from harbor.core.drafting import DiaryDrafter, LLMNotConfiguredError
from harbor.core.init_wizard import InitWizard, InitWizardOptions
from harbor.core.decorator import DecoratorEngine
from harbor.core.workspace import load_workspace_config, load_workspace_paths, write_workspace_config


def _is_log_write_interactive() -> bool:
    return bool(sys.stdin.isatty() and sys.stdout.isatty())


def _normalize_windows_stdio_encoding_name(value: Optional[str]) -> Optional[str]:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower().replace("_", "-")
    return normalized or None


def _is_utf8_compatible_stdio_encoding(value: Optional[str]) -> bool:
    return _normalize_windows_stdio_encoding_name(value) in {"utf-8", "utf8", "utf-8-sig"}


def _resolve_windows_explicit_stdio_config() -> Optional[Tuple[Optional[str], Optional[str]]]:
    explicit = os.environ.get("PYTHONIOENCODING", "").strip()
    if not explicit:
        return None

    encoding, sep, errors = explicit.partition(":")
    resolved_encoding = encoding.strip() or None
    resolved_errors = errors.strip() if sep else None
    return resolved_encoding, resolved_errors or None


def _is_pure_json_output_argv(argv) -> bool:
    """Detect pure JSON stdout routes from raw argv without changing parsing."""
    if not argv:
        return False

    tokens = [str(token) for token in argv]
    wants_json = False
    for index, token in enumerate(tokens):
        if token == "--format" and index + 1 < len(tokens):
            wants_json = tokens[index + 1] == "json"
            continue
        if token.startswith("--format="):
            wants_json = token.partition("=")[2] == "json"
    if not wants_json:
        return False

    non_option_tokens = [token for token in tokens if token != "--" and not token.startswith("-")]
    if not non_option_tokens:
        return False

    command = non_option_tokens[0]
    subcommand = non_option_tokens[1] if len(non_option_tokens) > 1 else None
    pure_json_commands = {"accept", "checkpoint", "doctor", "next", "stale", "verify-generated"}
    if command in pure_json_commands:
        return True
    if command == "log" and subcommand == "draft":
        return True
    if command == "workspace" and subcommand in {"inspect", "migrate"}:
        return True
    return False


def _resolve_windows_stdio_target(
    stream, *, preserve_native_encoding: bool = False
) -> Optional[Tuple[Optional[str], Optional[str]]]:
    """Resolve the preferred Windows stdio strategy for one CLI output stream."""
    explicit = _resolve_windows_explicit_stdio_config()
    if explicit is not None:
        return explicit

    if preserve_native_encoding:
        return None

    if os.environ.get("PYTHONUTF8") == "1" or getattr(sys.flags, "utf8_mode", 0):
        return "utf-8", "strict"

    try:
        is_tty = bool(stream.isatty())
    except Exception:
        return None

    if is_tty:
        if _is_utf8_compatible_stdio_encoding(getattr(stream, "encoding", None)):
            return None
        return "utf-8", "strict"

    return "utf-8", "strict"


def _resolve_windows_redirected_stdio_encoding(stream) -> Optional[str]:
    """Backward-compatible access to the resolved Windows stdio encoding."""
    target = _resolve_windows_stdio_target(stream)
    if target is None:
        return None
    return target[0]


def _configure_windows_stdio(argv=None) -> None:
    """Apply a Windows CLI-wide UTF-8-first stdio strategy when possible."""
    if os.name != "nt":
        return
    pure_json_stdout = _is_pure_json_output_argv(argv)
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is None or not hasattr(stream, "reconfigure"):
            continue
        try:
            target_encoding, target_errors = _resolve_windows_stdio_target(
                stream,
                preserve_native_encoding=(pure_json_stdout and name == "stdout"),
            ) or (None, None)
            if target_encoding is None and target_errors is None:
                continue

            current_encoding = getattr(stream, "encoding", None)
            current_errors = getattr(stream, "errors", None)
            same_encoding = (
                target_encoding is None
                or _normalize_windows_stdio_encoding_name(current_encoding)
                == _normalize_windows_stdio_encoding_name(target_encoding)
            )
            same_errors = target_errors is None or current_errors == target_errors
            if same_encoding and same_errors:
                continue

            kwargs = {}
            if target_encoding is not None:
                kwargs["encoding"] = target_encoding
            if target_errors is not None:
                kwargs["errors"] = target_errors
            if not kwargs:
                continue

            stream.reconfigure(**kwargs)
        except Exception:
            continue


def _configure_redirected_windows_stdio(argv=None) -> None:
    """Backward-compatible wrapper for the Windows CLI-wide stdio policy."""
    _configure_windows_stdio(argv=argv)


def _emit_json_stdout(payload) -> None:
    """Write one JSON object to stdout with an ASCII-safe fallback when needed."""
    localized_json = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
    stdout = getattr(sys, "stdout", None)
    stdout_encoding = getattr(stdout, "encoding", None) or "utf-8"
    try:
        localized_json.encode(stdout_encoding, errors="strict")
        rendered = localized_json
    except (LookupError, UnicodeEncodeError):
        rendered = json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2)

    if stdout is None:
        print(rendered)
        return

    stdout.write(rendered)
    stdout.write("\n")


def main():
    """Harbor CLI entrypoint and public command dispatch contract.

    This function parses `harbor` arguments and dispatches workflow, check/gate,
    and write commands to subcommand handlers.

    Behavior:
      - Legacy `harbor log -m/--message` and `harbor log --summary` remain
        compatible summary-input aliases for direct Diary logging.
      - Legacy `harbor log -m ... --type decision` is supported alongside the
        previously accepted legacy `type=chore` path.
      - Direct legacy `harbor log -m/--message` validation errors for invalid
        `type` / `importance` / `visibility` or missing summary are rendered as
        friendly CLI errors for caller-visible handling.
      - Invalid legacy `harbor log` args exit with code 1 and must not print a
        Python traceback in normal CLI output.
      - On Windows, human-readable text routes retain the CLI-wide UTF-8-first
        stdio strategy for localized output across redirected outputs and
        eligible interactive TTY streams unless the caller explicitly overrides
        stdio encoding with `PYTHONIOENCODING`.
      - Pure JSON stdout routes detected from raw argv (for example
        `checkpoint --ci --format json`) preserve native/host-compatible
        `stdout` behavior on Windows unless the caller explicitly overrides
        stdio encoding with `PYTHONIOENCODING`; `stderr` keeps the existing
        UTF-8-first policy for localized diagnostics.
      - This Windows pure-JSON stdout carve-out avoids PowerShell 5.1 native
        command display / redirection corruption while keeping machine-readable
        JSON payload keys, value shape, command routing, and exit-code
        semantics unchanged.
      - Pure JSON stdout first renders localized JSON with
        `ensure_ascii=False`; when the active `stdout` encoding cannot encode
        the full localized payload, Harbor automatically falls back to
        ASCII-escaped JSON for that write only so stdout remains one parseable
        JSON object without changing payload semantics, routing, or exit codes.
      - `harbor log draft` / `harbor log write` dispatch order remains explicit:
        draft/write subcommands are handled before legacy direct `harbor log`
        message or LLM-assisted draft flows.
      - `checkpoint` / `stale` / `doctor` support `--advice off|basic`.
      - `finish --sync-context` refreshes changed modules plus any indexed
        parent aggregate modules so module-level L2 README / Capsule views stay
        aligned when a nested module change also affects an ancestor summary.
      - `finish --sync-context`, `docs --changed`, `module seal --changed`,
        `stale --changed`, `stale --ci`, and `doctor --changed` share the same
        changed-scope resolver for changed-module detection, repo-relative path
        normalization, and indexed parent aggregate expansion.
      - Generated-context write paths plus `stale` / `doctor` module discovery
        and stale-validation paths prefer the same fresh/source-derived
        readonly index truth before falling back to local runtime cache
        snapshots, reducing local-cache versus clean-CI drift.
      - Fresh/source-compatible helper wrappers in these CLI routes preserve
        existing user-visible command semantics while keeping legacy internal
        call sites monkeypatch-compatible.
      - After writing changed-scope L2 README and Module Capsule outputs,
        `finish --sync-context` runs a same-scope stale self-check.
      - When the self-check passes, `finish --sync-context` prints an explicit
        same-scope completion message and keeps its original success semantics.
      - When residual stale remains after sync, `finish --sync-context` prints
        module / view / status / reason rows and deterministic repair guidance
        instead of ending silently.
      - When changed files hit generator / integrity core files,
        `finish --sync-context` prints a broader-refresh advisory recommending
        explicit `harbor docs --all --write` and `harbor module seal --all
        --write`, but does not run full refresh automatically.
      - These `finish --sync-context` enhancements do not relax
        `stale --ci`, do not change `checkpoint` / `doctor` gate semantics, do
        not auto-refresh project structure, and do not auto-run docs/module
        `--all` write paths.
      - Successful `checkpoint` / `accept` / `finish` dispatch paths also attempt
        to write lightweight change-window runtime snapshots under
        `.harbor/state/change-windows/`.
      - Change-window snapshots are runtime state only, not source of truth, and
        provide evidence for future `harbor log draft` workflows.
      - Snapshot write failure must not change the original command `exit_code`
        or gate result.
      - Snapshot write failure may append runtime-only diagnostics under
        `.harbor/state/change-window-diagnostics.jsonl` without changing
        normal CLI output.
      - Change-window snapshots do not write Diary entries and do not
        automatically execute `harbor log`.
      - `harbor log draft` is a safe read-only draft generator:
        it summarizes existing evidence to stdout / optional non-diary output
        paths and does not write `.harbor/diary/**`.
      - Default `harbor log draft` evidence boundary is marker-first:
        `last_log_marker` -> latest accept fallback -> recent snapshots fallback.
      - `harbor log draft` supports `--since-last-accept`,
        `--since-last-log`, `--from-report <path>`,
        `--format markdown|json`, `--output <path>`, and `--save`.
      - Draft JSON output keeps stdout as one pure JSON object and includes
        additive boundary metadata fields:
        `boundary_source`, `boundary_timestamp`, `boundary_note`, and
        `draft_status`; successful JSON mode does not append human hints on
        stderr.
      - `harbor log draft --output` may write one non-diary file such as
        `.harbor/reports/*.md` or `.harbor/reports/*.json`.
      - Successful non-JSON `harbor log draft` output prints localized next
        actions for formal Diary write/save flows only when the current evidence
        is sufficient to generate a writable Diary Draft.
      - Redirected stdio encoding normalization must not change CLI arguments,
        exit-code semantics, JSON payload structure, file-write targets, or
        `stderr` semantics; the Windows pure-JSON stdout compatibility
        carve-out changes only stdio configuration policy, not JSON business
        fields or parser behavior.
      - `harbor log draft` refreshes latest draft runtime cache under
        `.harbor/state/log/latest-draft.md` and
        `.harbor/state/log/latest-draft.json` only when it produced a writable
        Diary Draft; insufficient-evidence no-op drafts do not refresh latest
        draft cache.
      - Latest draft cache writes are runtime state only, may overwrite prior
        cache files, and must not change stdout draft content or exit semantics
        if cache write fails.
      - `harbor log draft --save` may write one timestamped non-diary report
        copy under `.harbor/reports/`; if both `--save` and `--output` are
        present, explicit `--output` takes precedence.
      - `harbor log draft` never executes `harbor log`, never writes
        `.harbor/diary/**`, never writes `last_log_marker`, and never calls LLM.
      - `--since-last-log` forces the log-marker boundary path; if the marker is
        unavailable or invalid, draft output keeps an explicit fallback /
        uncertainty note instead of silently pretending a precise boundary.
      - `--since-last-accept` forces the latest accept boundary and does not use
        `last_log_marker` for that explicit mode.
      - `harbor log draft` / `harbor log write` expose only summary-level draft
        data and never print file bodies or diff bodies.
      - `harbor log write` writes source-of-truth Diary memory only after
        explicit authorization through `--yes` or interactive confirmation.
      - `harbor log write` reads the latest draft cache by default, supports
        `--from-latest-draft` and approved `--from-draft <path>` sources, and
        rejects `.harbor/diary/**`, `.env*`, `secrets/**`, outside-repo paths,
        and traversal attempts.
      - No real Diary write occurs unless the user explicitly invokes a write
        path (`harbor log -m/--message` or `harbor log write ...`) that reaches
        canonical `.harbor/diary/**` append logic.
      - Successful `harbor log write` appends one structured JSON line to
        `.harbor/diary/YYYY-MM.jsonl` and then attempts a best-effort
        `.harbor/state/log/last_log_marker.json` update.
      - Default successful `harbor log write` stdout is a concise localized
        summary, not the full written JSON entry payload.
      - Non-interactive `harbor log write` requires `--yes`; cancel/deny paths
        must not write `.harbor/diary/**`.
      - `init` supports `--advice off|basic` and writes advice defaults into
        `.harbor/config/harbor.yaml` through initializer logic.
      - `checkpoint --ci` 以 repo-owned accepted baseline artifact
        `.harbor/baseline/accepted-checkpoint.json` 作为正式 CI baseline truth。
      - `checkpoint --ci` 会稳定输出 `baseline_source` / `baseline_path` /
        `baseline_found` 三个 baseline 字段，并在 `summary` / `ci_failures`
        中暴露 accepted artifact 缺失或非法的 gate 结果。
      - accepted artifact 缺失时，`checkpoint --ci` 使用
        `accepted_baseline_missing` 阻断分类；artifact 非法时使用
        `accepted_baseline_invalid` 阻断分类。
      - `checkpoint --ci` 在 accepted artifact 缺失或非法时不会回退到
        runtime cache；相关 baseline 字段语义保持稳定，便于 CI / agent 消费。
      - `checkpoint --ci` may emit TypeScript MVP advisory category
        `unsupported_syntax_advisory` as non-blocking output.
      - `verify-generated` dispatches exactly one scope route per invocation:
        `--module <path>`, `--changed` (default changed-module scope), or
        `--all`; conflicting mode flags fail through parser validation without
        changing other CLI routing contracts.
      - `verify-generated --format json` emits the public verify-generated JSON
        payload; `verify-generated --ci --format json` emits the generic CI JSON
        envelope with unchanged single-object stdout routing and non-zero exit
        semantics only when blocking generated-artifact failures are present.
      - `next --from <report.json>` supports `--format text|json`.
      - `next` guidance generation for checkpoint items is language-aware
        (for example, TypeScript categories use deterministic TS-specific advice).
      - Guidance for `--advice basic` is deterministic metadata and does not use
        LLM/provider calls.
      - Guidance is optional additive data and does not change
        `exit_code` / `ci_failures` / advisory gate semantics.
      - Change-window snapshot support does not change `checkpoint` / `finish` /
        `accept` gate semantics.
      - `harbor next` is read-only: does not write files, does not execute fix
        commands, does not call LLM, and does not accept baseline.
      - `--format json` outputs for CI/next commands remain a single JSON object
        on stdout (no mixed human text in the JSON stream).
      - `harbor check --format jsonl` is intentionally mixed output (DDT text
        sections plus semantic-audit JSONL lines), not pure JSONL-only stdout.

    Side Effects:
      - Depends on subcommand. Gate commands are read-only by contract; write
        commands such as `lock` / `log` / `docs --write` may write files.
      - `finish --sync-context` may write derived L2 README / Module Capsule
        views for changed modules and indexed parent aggregate modules.
      - `checkpoint` / `accept` / `finish` may additionally write change-window
        runtime state under `.harbor/state/change-windows/`.

    Returns:
      None: Dispatches the selected CLI command. On Windows, successful
      human-readable text routes retain UTF-8-first localized output behavior,
      while successful pure JSON stdout routes preserve host-compatible
      `stdout` behavior unless the caller explicitly overrides stdio encoding
      via `PYTHONIOENCODING`; localized JSON is emitted when the active stdout
      encoding can represent the payload and otherwise falls back to
      ASCII-escaped JSON so the write remains one machine-readable JSON object.
      These stdio-policy differences do not change JSON keys, value shape,
      command routing, exit semantics, or `stderr` semantics. Change-window snapshot writes
      are additive runtime state only and do not change the original command
      exit semantics. Snapshot write failures may append runtime-only
      diagnostics under `.harbor/state/change-window-diagnostics.jsonl`.
      `finish --sync-context` reuses the shared changed-scope resolver used by
      `docs --changed`, `module seal --changed`, `stale --changed`,
      `stale --ci`, and `doctor --changed`; after writing changed-scope L2
      README / Module Capsule outputs it reports either an explicit same-scope
      stale self-check pass or residual stale rows with deterministic repair
      guidance. Generated-context write paths plus `stale` / `doctor`
      enumeration paths use fresh/source-compatible readonly index helpers to
      reduce local-cache versus clean-CI drift. Generator / integrity file hits
      add advisory text recommending explicit `harbor docs --all --write` and
      `harbor module seal --all --write` only; they do not trigger automatic
      full refresh, project-structure refresh, or gate-semantic changes for
      `checkpoint` / `stale` / `doctor`.
      `harbor log draft` emits a reviewable markdown/json draft only, may write
      latest draft runtime cache under `.harbor/state/log/latest-draft.*` only
      when evidence is sufficient for a writable draft, may write one non-diary
      output file such as `.harbor/reports/*.md` or `.harbor/reports/*.json`
      via `--output` or `--save`, does not write `.harbor/diary/**`, does not
      update log markers, does not read or print file bodies / diff bodies, and
      does not call LLM. Draft JSON output keeps stdout as one pure JSON object
      and may include additive boundary metadata fields `boundary_source`,
      `boundary_timestamp`, `boundary_note`, and `draft_status`. Successful
      `checkpoint --ci --format json` emits one pure JSON object whose baseline
      contract includes `baseline_source`, `baseline_path`, and
      `baseline_found`; accepted artifact failures are reported as
      `accepted_baseline_missing` / `accepted_baseline_invalid` without
      changing the non-write gate contract.
      Successful text-mode `checkpoint --ci` prints the same accepted artifact
      baseline semantics in human-readable form while preserving gate behavior.
      Successful
      non-JSON `harbor log draft` stdout appends localized next-action hints
      only for writable drafts. `draft_status="insufficient_evidence"` is a
      no-op draft result: stdout remains reviewable, latest draft cache is not
      refreshed, and no `harbor log write` hint is appended. Draft `--output` /
      `--save` write targets remain non-diary reports only and do not change
      source-of-truth Diary semantics. `.harbor/diary/**` is the canonical
      Diary area rather than production code classification. `harbor log write`
      may append one structured JSON line to `.harbor/diary/YYYY-MM.jsonl` and may update
      `.harbor/state/log/last_log_marker.json` after successful write;
      successful default stdout is a concise localized summary rather than the
      full written JSON entry payload, while written JSONL entry content
      remains unchanged.

    Raises:
      SystemExit: Propagates CLI parse failures and CI/gate exit codes from the
      primary command flow. Snapshot write failures must not raise a different
      exit outcome and must not surface as normal CLI output. `harbor log draft`
      argument / path / report-parse errors fail clearly without writing Diary;
      latest draft cache write failures remain non-fatal warnings only. `harbor
      log write` read/authorization/path errors fail clearly without writing
      Diary; direct legacy `harbor log -m/--message` validation failures also
      fail clearly without traceback-driven UX; marker update failures do not
      roll back a completed Diary write. Non-interactive `harbor log write`
      still requires explicit `--yes` authorization unless the user confirms in
      an interactive session; cancel/deny paths must not write
      `.harbor/diary/**`. Windows stdio normalization and the pure-JSON stdout
      compatibility carve-out do not introduce a new blocking exception path;
      when the active stdout encoding cannot represent localized JSON, Harbor
      falls back to ASCII-escaped JSON instead of raising `UnicodeEncodeError`.
      These paths do not change command routing, JSON payload semantics, or
      `stderr` semantics. These UX-polish paths do not call LLM, do not print
      file bodies / diff bodies / secrets. `finish --sync-context` stale
      self-check and generator/integrity advisory remain guidance/output
      behavior only: they do not introduce a new blocking exception path, do
      not change `checkpoint` / `stale` / `doctor` gate semantics, and do not
      auto-run project-structure refresh or docs/module `--all` writes. Legacy
      `harbor log` behavior remains unchanged.

    @harbor.scope: public
    @harbor.l3_strictness: strict
    @harbor.idempotency: once
    @harbor.behavior: Windows human-readable text routes retain CLI-wide UTF-8-first localized output behavior unless the caller explicitly overrides stdio encoding with `PYTHONIOENCODING`; Windows pure JSON `--format json` stdout routes preserve host-compatible `stdout` behavior unless explicitly overridden, avoiding PowerShell 5.1 native-command display/redirection corruption without changing JSON keys, value shape, exit codes, command routing, or `stderr` semantics; pure JSON writes first render localized JSON and automatically fall back to ASCII-escaped JSON only when the active stdout encoding cannot strictly encode the payload, preventing `UnicodeEncodeError` while keeping stdout as one parseable JSON object with unchanged payload semantics; checkpoint/next support deterministic TypeScript MVP guidance (`contract_gap`/`skipped_no_contract`/`unsupported_syntax_advisory`) without auto-fix and without changing CI gate semantics; `verify-generated` routes exactly one scope per invocation (`--module`, changed default, or `--all`), preserves parser-level mutual-exclusion failures for conflicting mode flags, and keeps text/json/ci output routing additive to the existing public CLI dispatch contract; `verify-generated --ci --format json` reuses the generic CI JSON envelope and changes exit status only when blocking generated-artifact failures are present; `finish --sync-context`, `docs --changed`, `module seal --changed`, `stale --changed`, `stale --ci`, and `doctor --changed` share one changed-scope resolver for changed-module detection, repo-relative normalization, and indexed parent aggregate expansion; generated-context write paths plus `stale` / `doctor` enumeration paths use fresh/source-compatible readonly index helpers to reduce local-cache versus clean-CI drift without changing user-visible CLI routing semantics; `finish --sync-context` writes changed-scope L2 README / Module Capsule outputs, then runs a same-scope stale self-check that prints an explicit pass message or residual stale rows with deterministic repair guidance; generator / integrity file hits print broader-refresh advisory text recommending explicit `harbor docs --all --write` and `harbor module seal --all --write` only, without auto-running full refresh or project-structure refresh; docs/module batch flows reject outside-repo absolute module paths and display skipped unsafe modules with sanitized `<outside-repo>` placeholders; successful non-JSON `harbor log draft` distinguishes writable `draft_status=ready` from no-op `draft_status=insufficient_evidence`; no-op drafts skip latest-draft cache refresh and suppress localized `harbor log write` hints, while `--format json` keeps stdout as one JSON object with no extra human text; existing `harbor log write` authorization and marker-update boundaries remain unchanged; successful `harbor log write` prints a concise localized success summary instead of the full written JSON entry payload.
    """
    _configure_windows_stdio(sys.argv[1:])

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    def _map_argv(argv):
        if not argv:
            return argv, None
        tokens = list(argv)
        dep = None
        if tokens[0] == "build-index":
            tokens[0] = "lock"
            dep = "build-index"
        elif tokens[0] == "audit":
            dep = "audit"
            tokens[0] = "check"
        elif tokens[0] == "diary":
            if len(tokens) >= 2:
                subc = tokens[1]
                dep = f"diary {subc}"
                if subc == "draft":
                    tokens = ["log"] + tokens[2:]
                elif subc == "log":
                    tokens = ["log"] + tokens[2:]
                elif subc == "export":
                    tokens = ["log", "--export"] + tokens[2:]
        elif tokens[0] == "gen":
            if len(tokens) >= 2 and tokens[1] == "l2":
                tokens = ["docs"] + tokens[2:]
                dep = "gen l2"
        elif tokens[0] == "decorate":
            tokens[0] = "adopt"
            dep = "decorate"
        elif tokens[0] == "ddt":
            if len(tokens) >= 2 and tokens[1] == "validate":
                tokens = ["check", "--fast"] + tokens[2:]
                dep = "ddt validate"
        elif tokens[0] == "st":
            tokens[0] = "status"
        elif tokens[0] == "conf":
            tokens[0] = "config"
        elif tokens[0] == "commit":
            tokens[0] = "lock"
        return tokens, dep

    argv_mapped, deprecated = _map_argv(sys.argv[1:])

    parser = argparse.ArgumentParser(prog="harbor", description="Harbor-spec CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_lock = sub.add_parser("lock", help="Low-level runtime cache/index rebuild command")
    p_lock.add_argument("--no-incremental", action="store_true")
    p_lock.add_argument("--code-root", action="append", default=None)
    p_lock.add_argument("--cache-dir", type=str, default=None)
    p_lock.add_argument("--no-register-adopted", action="store_true")
    p_lock.add_argument("--register-scan", action="store_true")

    p_config = sub.add_parser("config", help="Manage Harbor config")
    p_cfg_sub = p_config.add_subparsers(dest="cfg_cmd", required=True)
    p_cfg_list = p_cfg_sub.add_parser("list", help="List current config values")
    p_cfg_add = p_cfg_sub.add_parser("add", help="Add a path to code_roots")
    p_cfg_add.add_argument("path", type=str)
    p_cfg_remove = p_cfg_sub.add_parser("remove", help="Remove a path from code_roots")
    p_cfg_remove.add_argument("path", type=str)
    p_cfg_adopted = p_cfg_sub.add_parser("adopted", help="Show or write derived adopted roots")
    p_cfg_adopted.add_argument("--write", action="store_true")
    p_cfg_adopted.add_argument("--min-count", type=int, default=5)

    p_status = sub.add_parser("status", help="Show Harbor context status (no implicit index update)")
    p_status.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed non-blocking items",
    )
    p_start = sub.add_parser(
        "start",
        help="Workflow facade: run status before AI coding",
        description="Workflow facade command: run status before AI coding.",
    )
    p_checkpoint = sub.add_parser(
        "checkpoint",
        help="Workflow facade: status + check --fast",
        description="Workflow facade command: run status + check --fast.",
    )
    p_checkpoint.add_argument(
        "--ci",
        action="store_true",
        help="Enable CI gate mode with deterministic exit code semantics",
    )
    p_checkpoint.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format for CI mode only: text (default) or json",
    )
    p_checkpoint.add_argument(
        "--advice",
        type=str,
        choices=["off", "basic"],
        default=None,
        help="Repair guidance mode override: off or basic",
    )
    p_finish = sub.add_parser(
        "finish",
        help="Workflow facade: status + check + next steps",
        description="Workflow facade command: run status + check and print guided next steps.",
    )
    p_finish.add_argument(
        "--sync-context",
        action="store_true",
        help="Run finish checks and sync derived context views for changed modules",
    )
    p_finish.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed non-blocking items",
    )
    p_accept = sub.add_parser(
        "accept",
        help="Accept current checkpoint baseline into repository baseline artifact",
        description="Write the accepted checkpoint baseline artifact and optionally refresh runtime cache.",
    )
    p_accept.add_argument(
        "--output",
        type=str,
        default=None,
        help="Write accepted checkpoint baseline artifact to a custom path",
    )
    p_accept.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format: text (default) or json",
    )
    p_accept.add_argument(
        "--no-cache-refresh",
        action="store_true",
        help="Write the accepted baseline artifact without refreshing runtime cache",
    )

    p_adopt = sub.add_parser("adopt", help="Adopt legacy code into Harbor governance")
    p_adopt.add_argument("path", type=str)
    p_adopt.add_argument("--strategy", type=str, choices=["safe", "aggressive"], default="safe")
    p_adopt.add_argument("--yes", action="store_true")
    p_adopt.add_argument("--dry-run", action="store_true")
    p_unadopt = sub.add_parser("unadopt", help="Remove adopted directory from Harbor code_roots")
    p_unadopt.add_argument("path", type=str)

    p_check = sub.add_parser("check", help="Run semantic and DDT checks")
    p_check.add_argument("--fast", action="store_true")
    p_check.add_argument("--module", type=str, default=None)
    p_check.add_argument("--func", type=str, default=None)
    p_check.add_argument("--diff-only", action="store_true", default=True)
    p_check.add_argument("--debug", action="store_true", default=False)
    p_check.add_argument("--format", type=str, choices=["plain", "jsonl"], default="jsonl")
    p_check.add_argument("--verbose", action="store_true", help="Show detailed advisory and semantic output")

    p_docs = sub.add_parser(
        "docs",
        help="Generate L2 README for a module",
        description=(
            "Generate Anchor (L2) README for module(s).\n\n"
            "Examples:\n"
            "  harbor docs --module harbor/core\n"
            "  harbor docs --module harbor/core --write\n"
            "  harbor docs --changed --write\n"
            "  harbor docs --all --write\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p_docs.add_argument(
        "--module",
        type=str,
        help="Target module directory (e.g. harbor/core) to generate L2 view",
    )
    p_docs.add_argument(
        "--changed",
        action="store_true",
        help="Detect changed modules and generate L2 view for each",
    )
    p_docs.add_argument(
        "--all",
        dest="all_modules",
        action="store_true",
        help="Generate L2 view for all indexed modules",
    )
    p_docs.add_argument(
        "--write",
        action="store_true",
        help="Write canonical L2 README under .harbor/views/l2/<module>/README.md (and optional <module>/README.md export); default prints Markdown to console",
    )
    p_docs.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite of canonical/export README targets when used with --write",
    )
    p_stale = sub.add_parser(
        "stale",
        help="Check stale status of derived context views (L2 README + Module Capsule)",
    )
    p_stale.add_argument(
        "--module",
        type=str,
        help="Target module directory (e.g. harbor/core)",
    )
    p_stale.add_argument(
        "--changed",
        action="store_true",
        help="Detect changed modules and check stale status for each",
    )
    p_stale.add_argument(
        "--all",
        dest="all_modules",
        action="store_true",
        help="Check stale status for all indexed modules",
    )
    p_stale.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format: text (default) or json",
    )
    p_stale.add_argument(
        "--ci",
        action="store_true",
        help="Enable CI gate mode with deterministic exit code semantics",
    )
    p_stale.add_argument(
        "--advice",
        type=str,
        choices=["off", "basic"],
        default=None,
        help="Repair guidance mode override: off or basic",
    )
    p_doctor = sub.add_parser(
        "doctor",
        help="Run read-only aggregated Harbor health checks",
    )
    p_doctor.add_argument(
        "--module",
        type=str,
        help="Target module directory (e.g. harbor/core)",
    )
    p_doctor.add_argument(
        "--changed",
        action="store_true",
        help="Detect changed modules and run doctor checks in changed scope",
    )
    p_doctor.add_argument(
        "--all",
        dest="all_modules",
        action="store_true",
        help="Run doctor checks for all indexed modules",
    )
    p_doctor.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format: text (default) or json",
    )
    p_doctor.add_argument(
        "--ci",
        action="store_true",
        help="Enable CI gate mode with deterministic exit code semantics",
    )
    p_doctor.add_argument(
        "--advice",
        type=str,
        choices=["off", "basic"],
        default=None,
        help="Repair guidance mode override: off or basic",
    )
    p_verify_generated = sub.add_parser(
        "verify-generated",
        help="Verify that tracked generated context is reproducible from current source truth",
    )
    p_verify_generated.add_argument(
        "--module",
        type=str,
        help="Target module directory (e.g. harbor/core)",
    )
    p_verify_generated.add_argument(
        "--changed",
        action="store_true",
        help="Detect changed modules and verify generated artifacts for each",
    )
    p_verify_generated.add_argument(
        "--all",
        dest="all_modules",
        action="store_true",
        help="Verify generated artifacts for all indexed modules",
    )
    p_verify_generated.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format: text (default) or json",
    )
    p_verify_generated.add_argument(
        "--ci",
        action="store_true",
        help="Enable CI gate mode with deterministic exit code semantics",
    )
    p_verify_generated.add_argument(
        "--advice",
        type=str,
        choices=["off", "basic"],
        default=None,
        help="Repair guidance mode override: off or basic",
    )
    p_next = sub.add_parser(
        "next",
        help="Read Harbor JSON report and print conservative next actions (read-only)",
    )
    p_next.add_argument(
        "--from",
        dest="from_path",
        required=True,
        type=str,
        help="Path to checkpoint/stale/doctor JSON report",
    )
    p_next.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format: text (default) or json",
    )
    p_next.add_argument(
        "--advice",
        type=str,
        choices=["off", "basic"],
        default=None,
        help="Repair guidance mode override: off or basic",
    )
    p_next.add_argument(
        "--max-items",
        type=int,
        default=20,
        help="Maximum items to display",
    )
    p_workspace = sub.add_parser(
        "workspace",
        help="Workspace layout inspection commands",
    )
    p_workspace_sub = p_workspace.add_subparsers(dest="workspace_cmd", required=True)
    p_workspace_inspect = p_workspace_sub.add_parser(
        "inspect",
        help="Inspect current Harbor workspace layout (read-only advisory)",
    )
    p_workspace_inspect.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format: text (default) or json",
    )
    p_workspace_migrate = p_workspace_sub.add_parser(
        "migrate",
        help="Generate workspace migration plan (dry-run only in current phase)",
    )
    p_workspace_migrate.add_argument(
        "--dry-run",
        action="store_true",
        help="Print migration plan only. No files are changed.",
    )
    p_workspace_migrate.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format: text (default) or json",
    )

    p_module = sub.add_parser(
        "module",
        help="Inspect or generate module capsule for one module",
    )
    p_module_sub = p_module.add_subparsers(dest="module_cmd", required=True)
    p_module_inspect = p_module_sub.add_parser(
        "inspect",
        help="Inspect indexed context for one module",
    )
    p_module_inspect.add_argument("module", type=str)
    p_module_seal = p_module_sub.add_parser(
        "seal",
        help="Preview or write module capsule for one module, changed modules, or all indexed modules",
    )
    p_module_seal.add_argument(
        "module",
        nargs="?",
        type=str,
        help="Target module directory (e.g. harbor/core)",
    )
    p_module_seal.add_argument(
        "--changed",
        action="store_true",
        help="Detect changed modules and generate module capsule for each",
    )
    p_module_seal.add_argument(
        "--all",
        dest="all_modules",
        action="store_true",
        help="Generate module capsule for all indexed modules",
    )
    p_module_seal.add_argument(
        "--write",
        action="store_true",
        help="Write capsule files under .harbor/views/modules/<module>/ (and optional docs export if enabled)",
    )
    p_module_stale = p_module_sub.add_parser(
        "stale",
        help="Check whether module capsule is stale for one module, changed modules, or all indexed modules",
    )
    p_module_stale.add_argument(
        "module",
        nargs="?",
        type=str,
        help="Target module directory (e.g. harbor/core)",
    )
    p_module_stale.add_argument(
        "--changed",
        action="store_true",
        help="Detect changed modules and check stale status for each",
    )
    p_module_stale.add_argument(
        "--all",
        dest="all_modules",
        action="store_true",
        help="Check stale status for all indexed modules",
    )
    p_module_promote = p_module_sub.add_parser(
        "promote-skill",
        help="Generate a thin optional skill entrypoint for one module",
    )
    p_module_promote.add_argument("module", type=str)

    p_project = sub.add_parser(
        "project",
        help="Project-level derived views",
    )
    p_project_sub = p_project.add_subparsers(dest="project_cmd", required=True)
    p_project_structure = p_project_sub.add_parser(
        "structure",
        help="Preview or write derived project structure view",
    )
    p_project_structure.add_argument(
        "--write",
        action="store_true",
        help="Write canonical .harbor/views/project-structure.md (and optional docs export if enabled); default prints preview",
    )

    p_log = sub.add_parser(
        "log",
        help="Context-aware diary logging",
        description=(
            "Context-aware diary logging.\n\n"
            "Write target: .harbor/diary/YYYY-MM.jsonl (canonical).\n"
            "Legacy path specs/diary/YYYY-MM.jsonl is read-compatible only.\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p_log.add_argument("-m", "--message", type=str, required=False)
    p_log.add_argument("--summary", dest="message", type=str, required=False)
    p_log.add_argument("--type", type=str, default="feature")
    p_log.add_argument("--importance", type=str, default="normal")
    p_log.add_argument("--visibility", type=str, default="repo")
    p_log.add_argument("--details", type=str, default=None)
    p_log.add_argument("--ref-commit", type=str, default=None)
    p_log.add_argument("--author", type=str, default=None)
    p_log.add_argument("--ts", type=str, default=None)
    p_log.add_argument("--export", action="store_true")
    p_log.add_argument("--since", type=str, default=None)
    p_log_sub = p_log.add_subparsers(dest="log_cmd", required=False)
    p_log_draft = p_log_sub.add_parser(
        "draft",
        help="Generate a reviewable diary draft from existing change-window evidence",
    )
    p_log_draft_boundary = p_log_draft.add_mutually_exclusive_group()
    p_log_draft_boundary.add_argument(
        "--since-last-accept",
        action="store_true",
        help="Force change-window evidence after the latest accept snapshot",
    )
    p_log_draft_boundary.add_argument(
        "--since-last-log",
        action="store_true",
        help="Force `.harbor/state/log/last_log_marker.json` as the boundary; unavailable markers emit an explicit fallback note",
    )
    p_log_draft_boundary.add_argument(
        "--from-report",
        type=str,
        default=None,
        help="Use one explicit checkpoint/stale/doctor JSON report as draft evidence",
    )
    p_log_draft.add_argument(
        "--format",
        type=str,
        choices=["markdown", "json"],
        default="markdown",
        help="Draft output format",
    )
    p_log_draft.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional output path for the rendered draft; `.harbor/diary/**` is forbidden",
    )
    p_log_draft.add_argument(
        "--save",
        action="store_true",
        help="Save one timestamped report copy under `.harbor/reports/` unless `--output` is provided",
    )
    p_log_write = p_log_sub.add_parser(
        "write",
        help="Write one structured diary entry from the latest or an approved draft source",
    )
    p_log_write.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation and treat this as explicit write authorization",
    )
    p_log_write_source = p_log_write.add_mutually_exclusive_group()
    p_log_write_source.add_argument(
        "--from-draft",
        type=str,
        default=None,
        help="Read one approved draft file from `.harbor/reports/**` or `.harbor/state/log/latest-draft.*`",
    )
    p_log_write_source.add_argument(
        "--from-latest-draft",
        action="store_true",
        help="Explicitly read the latest draft cache under `.harbor/state/log/`",
    )

    p_init = sub.add_parser("init", help="Initialize Harbor via interactive setup wizard")
    p_init.add_argument("--force", action="store_true")
    p_init.add_argument("--dry-run", action="store_true")
    p_init.add_argument("--language", choices=["zh", "en"], default=None)
    p_init.add_argument("--project", choices=["new", "existing"], default=None)
    p_init.add_argument("--advice", choices=["off", "basic"], default=None)
    p_init_gov = p_init.add_mutually_exclusive_group()
    p_init_gov.add_argument("--governance", dest="governance", action="store_true")
    p_init_gov.add_argument("--no-governance", dest="governance", action="store_false")
    p_init.set_defaults(governance=None)
    p_init_gov_docs = p_init.add_mutually_exclusive_group()
    p_init_gov_docs.add_argument("--governance-docs", dest="governance_docs", action="store_true")
    p_init_gov_docs.add_argument("--no-governance-docs", dest="governance_docs", action="store_false")
    p_init.set_defaults(governance_docs=None)
    p_init_llm = p_init.add_mutually_exclusive_group()
    p_init_llm.add_argument("--llm", dest="llm", action="store_true")
    p_init_llm.add_argument("--no-llm", dest="llm", action="store_false")
    p_init.set_defaults(llm=None)
    p_init_gitignore = p_init.add_mutually_exclusive_group()
    p_init_gitignore.add_argument("--update-gitignore", dest="update_gitignore", action="store_true")
    p_init_gitignore.add_argument("--no-update-gitignore", dest="update_gitignore", action="store_false")
    p_init.set_defaults(update_gitignore=None)

    args = parser.parse_args(argv_mapped)

    def _load_cfg_data_safe():
        try:
            loaded = load_workspace_config(Path.cwd())
            return dict(loaded.get("config") or {})
        except Exception:
            return {}

    def _repo_display_path(path: Path) -> str:
        try:
            return path.resolve().relative_to(Path.cwd()).as_posix()
        except Exception:
            return path.resolve().as_posix()

    def _write_cfg_data(data):
        write_workspace_config(Path.cwd(), data)

    def _run_lock(*, code_roots=None, cache_dir=None, no_incremental=False, no_register_adopted=False, register_scan=False):
        builder = IndexBuilder(code_roots=code_roots, cache_dir=cache_dir)
        scanned = 0
        updated = 0
        skipped = 0
        items_total = 0
        console = Console()
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task_id = progress.add_task(t("cli.lock.init"), total=0)
            total_set = False
            for ev in builder.iter_build(incremental=not no_incremental):
                if not total_set:
                    progress.update(task_id, total=ev.total)
                    total_set = True
                if ev.status == "scanning":
                    progress.update(task_id, description=t("cli.lock.scanning", path=f"{ev.path}"))
                elif ev.status == "parsed":
                    scanned += 1
                    updated += 1
                    items_total += ev.items_count
                    progress.update(task_id, advance=1, description=t("cli.lock.done", path=f"{ev.path}"))
                elif ev.status == "skipped":
                    scanned += 1
                    skipped += 1
                    progress.update(task_id, advance=1, description=t("cli.lock.skipped", path=f"{ev.path}"))
                elif ev.status == "error":
                    scanned += 1
                    progress.update(task_id, advance=1, description=t("cli.lock.error", path=f"{ev.path}"))
        print(t("cli.lock.summary", scanned=scanned, updated=updated, skipped=skipped, items=items_total, db=builder.db.db_path.as_posix()))
        try:
            db = builder.db
            files = [fp for fp, _ in db.get_all_files()]
            cfg = _load_cfg_data_safe()
            excludes = cfg.get("exclude_paths", [])
            from harbor.core.utils import derive_adopted_roots
            derived = derive_adopted_roots(files, exclude_patterns=excludes, min_count=1)
            if not no_register_adopted and derived:
                adopted = cfg.get("adopted_roots", [])
                changed = False
                for p in derived:
                    if p not in adopted:
                        adopted.append(p)
                        changed = True
                # 可选：同时注册到扫描目录
                if register_scan:
                    roots = cfg.get("code_roots", [])
                    for p in derived:
                        if p not in roots:
                            roots.append(p)
                            changed = True
                    cfg["code_roots"] = roots
                if changed:
                    cfg["adopted_roots"] = adopted
                    _write_cfg_data(cfg)
                print(t("cli.lock.register_adopted_wrote", count=len(derived)))
            else:
                if derived:
                    print(t("cli.lock.register_adopted_hint"))
        except Exception:
            pass
        return {
            "scanned": scanned,
            "updated": updated,
            "skipped": skipped,
            "items": items_total,
            "code_roots": list(code_roots or []),
            "cache_dir": str(cache_dir) if cache_dir is not None else None,
            "no_incremental": bool(no_incremental),
            "register_scan": bool(register_scan),
        }

    def _collect_checkpoint_baseline_items():
        snapshot = SyncEngine().collect_current_snapshot()
        items = []
        for file_path in sorted(snapshot.keys()):
            for item_id in sorted(snapshot[file_path].keys()):
                item = dict(snapshot[file_path][item_id])
                items.append(
                    {
                        "id": str(item.get("id") or item.get("func_id") or ""),
                        "target_id": str(item.get("target_id") or ""),
                        "func_id": str(item.get("func_id") or item.get("id") or ""),
                        "language": str(item.get("language") or "python"),
                        "symbol_kind": str(item.get("symbol_kind") or "function"),
                        "file_path": str(item.get("file_path") or file_path),
                        "body_hash": str(item.get("body_hash") or ""),
                        "contract_hash": str(item.get("contract_hash") or ""),
                        "contract_presence": str(item.get("contract_presence") or "present"),
                        "contract_required": bool(item.get("contract_required")),
                    }
                )
        return items

    def _run_accept(*, output_path=None, no_cache_refresh=False):
        baseline_items = _collect_checkpoint_baseline_items()
        lock_summary = None
        if not no_cache_refresh:
            lock_summary = _run_lock()
        artifact = build_checkpoint_baseline_artifact(items=baseline_items)
        written_path = write_checkpoint_baseline_artifact(
            artifact,
            path=Path(output_path) if output_path else None,
        )
        return {
            "accepted": True,
            "artifact_written": True,
            "artifact_path": _repo_display_path(written_path),
            "artifact_items": len(artifact.get("baseline", {}).get("items", []) or []),
            "cache_refreshed": not no_cache_refresh,
            "cache_summary": lock_summary,
            "writes_files": True,
        }

    def _run_status(*, verbose=False):
        console = Console()
        with console.status(f"[bold blue]{t('cli.status.scanning')}", spinner="dots"):
            eng = SyncEngine()
            rep = eng.check_status()
        total = sum(rep.counts.values())
        if total == 0:
            print(t("cli.status.nochanges"))
            return rep, True
        print(t("cli.status.title"))
        if rep.drift:
            print(f"\n{t('cli.status.drift')}")
            for e in rep.drift:
                print(f"  M {e.id} ({e.details})")
        if rep.contract_changed:
            print(f"\n{t('cli.status.contract')}")
            for e in rep.contract_changed:
                print(f"  C {e.id} ({e.details})")
        if getattr(rep, "contract_gap", []):
            print("\nContract Gap")
            for e in rep.contract_gap:
                print(f"  G {e.id} ({e.details})")
        if getattr(rep, "skipped_no_contract", []):
            count = len(list(getattr(rep, "skipped_no_contract", []) or []))
            print(f"\n{t('cli.status.skipped_no_contract.summary', count=count)}")
            print(f"  {t('cli.status.skipped_no_contract.reason')}")
            if verbose:
                for e in rep.skipped_no_contract:
                    print(f"  S {e.id} ({e.details})")
            else:
                print(f"  {t('cli.common.use_verbose_details')}")
        if getattr(rep, "contract_parse_error", []):
            print("\nContract Parse Error")
            for e in rep.contract_parse_error:
                print(f"  E {e.id} ({e.details})")
        if getattr(rep, "unsupported_syntax_advisory", []):
            count = len(list(getattr(rep, "unsupported_syntax_advisory", []) or []))
            print(f"\nUnsupported Syntax Advisory: {count}")
            if verbose:
                for e in rep.unsupported_syntax_advisory:
                    print(f"  U {e.id} ({e.details})")
            else:
                print(f"  {t('cli.common.use_verbose_details')}")
        if rep.modified:
            print(f"\n{t('cli.status.modified')}")
            for e in rep.modified:
                print(f"  M {e.id} ({e.details})")
        if rep.untracked:
            print(f"\n{t('cli.status.untracked')}")
            for e in rep.untracked:
                print(f"  ? {e.id}")
        if rep.missing:
            print(f"\n{t('cli.status.missing')}")
            for e in rep.missing:
                print(f"  ! {e.id}")
        return rep, False

    def _print_checkpoint_contract_impact(rep):
        records = []
        records.extend(getattr(rep, "drift", []))
        records.extend(getattr(rep, "modified", []))
        records.extend(getattr(rep, "contract_changed", []))
        records.extend(getattr(rep, "contract_gap", []))
        records.extend(getattr(rep, "skipped_no_contract", []))
        records.extend(getattr(rep, "contract_parse_error", []))
        records.extend(getattr(rep, "untracked", []))
        records.extend(getattr(rep, "missing", []))
        if not records:
            return
        report = build_contract_impact_report(records)
        print("")
        print(format_contract_impact_report(report))
        print(t("cli.contract_impact.advisory_note"))

    def _build_checkpoint_snapshot_summary(*, status_report, check_summary, ci_result=None):
        counts = dict(getattr(status_report, "counts", {}) or {})
        ddt_violations = int((check_summary or {}).get("ddt_violations", 0))
        ci_failures = 0
        if ci_result is not None:
            status = str(getattr(ci_result, "status", "") or "pass").lower()
            ci_failures = len(list(getattr(ci_result, "ci_failures", []) or []))
        else:
            blocking_count = (
                int(counts.get("drift", 0))
                + int(counts.get("modified", 0))
                + int(counts.get("contract_changed", 0))
                + int(counts.get("contract_gap", 0))
                + int(counts.get("contract_parse_error", 0))
                + int(counts.get("untracked", 0))
                + int(counts.get("missing", 0))
                + ddt_violations
            )
            status = "fail" if blocking_count > 0 else "pass"
            ci_failures = blocking_count
        summary = {
            "status": status,
            "pass_fail": status,
            "counts": counts,
            "ci_failures": ci_failures,
            "ddt_violations": ddt_violations,
        }
        if check_summary:
            summary["check"] = dict(check_summary)
        return summary

    def _write_change_window_snapshot_safe(event, *, summary=None, validation=None, notes=None):
        try:
            write_change_window_snapshot(
                event,
                summary=summary or {},
                validation=validation or {},
                notes=notes or [],
                repo_root=Path.cwd(),
            )
        except Exception as exc:
            try:
                repo_root = Path.cwd()
                try:
                    workspace_paths = load_workspace_paths(repo_root, enforce_write_safety=True)
                    state_root = workspace_paths.state_root
                except Exception:
                    state_root = repo_root / ".harbor" / "state"
                diagnostics_path = state_root / "change-window-diagnostics.jsonl"
                intended_state_dir = state_root / "change-windows"
                diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
                command_context = None
                if isinstance(validation, dict):
                    command_context = str(validation.get("command") or "").strip() or None
                if command_context is None:
                    command_context = str(event or "").strip() or None
                record = {
                    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "event": str(event or "").strip().lower(),
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "cwd": repo_root.as_posix(),
                    "intended_state_dir": intended_state_dir.as_posix(),
                    "command_context": command_context,
                }
                with diagnostics_path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            except Exception:
                pass

    def _run_check(*, fast=False, module=None, func=None, diff_only=True, debug=False, output_format="jsonl", verbose=False):
        scanner = DDTScanner()
        bindings = scanner.scan_tests()
        if func:
            bindings = [b for b in bindings if b.func_id == func]
        if module:
            bindings = [b for b in bindings if b.func_id.startswith(module)]
        validator = DDTValidator()
        rep = validator.validate(bindings)
        print(t("cli.check.title"))
        print(f"\n{t('cli.check.ddt')}")
        print(t("cli.check.bindings", count=len(bindings)))
        baseline_missing_count = 0
        if rep.valid:
            if verbose:
                for b in rep.valid:
                    print(f"  OK {b.func_id} v={b.l3_version} strategy={b.strategy} ({b.test_name} @ {b.file_path})")
            else:
                print(f"  {t('cli.check.valid_summary', count=len(rep.valid))}")
        if rep.violations:
            for typ, b, msg in rep.violations:
                print(f"  [!] {typ.upper()} {b.func_id} v={b.l3_version} strategy={b.strategy} ({b.test_name} @ {b.file_path}) :: {msg}")
        if getattr(rep, "advisory", []):
            print(f"\n{t('cli.check.ddt_advisory')}")
            baseline_missing = [adv for adv in rep.advisory if str(getattr(adv, "category", "") or "") == "ddt_version_baseline_missing"]
            baseline_missing_count = len(baseline_missing)
            if baseline_missing and not verbose:
                print(f"  baseline-missing: {len(baseline_missing)} strict DDT bindings")
                print(f"  {t('cli.check.ddt_advisory.baseline_missing.line1')}")
                print(f"  {t('cli.check.ddt_advisory.baseline_missing.line2')}")
                print(f"  {t('cli.check.ddt_advisory.use_verbose_bindings')}")
            else:
                for adv in rep.advisory:
                    b = adv.binding
                    print(
                        "  - "
                        f"func_id={b.func_id} "
                        f"l3_version={b.l3_version} "
                        f"strategy={b.strategy} "
                        f"test_name={b.test_name} "
                        f"file_path={b.file_path}"
                    )
                    print(f"    {adv.message}")
        if not rep.valid and not rep.violations:
            print(f"  {t('cli.check.nobindings')}")
        semantic_targets_count = 0
        semantic_counts = {"OK": 0, "POSSIBLE_SEMANTIC_DRIFT": 0, "CONTRACT_GAP": 0, "SKIPPED_NO_CONTRACT": 0, "ERROR": 0}
        if not fast:
            eng = SyncEngine()
            status = eng.check_status()
            provider = resolve_provider()
            guard = SemanticGuard()
            model = getattr(provider, "model", "n/a")
            print(f"\n{t('cli.semantic.title')}")
            targets = []
            targets.extend(status.drift)
            targets.extend(status.modified)
            if not diff_only:
                targets.extend(status.contract_changed)
            semantic_targets_count = len(targets)
            print(f"targets={len(targets)}")
            out_lines = []
            for e in targets:
                try:
                    src = Path(e.file_path).read_text(encoding="utf-8")
                except Exception as ex:
                    if output_format == "jsonl":
                        print(json.dumps({
                            "status": "ERROR",
                            "func_id": e.id,
                            "file_path": e.file_path,
                            "reason": str(ex)
                        }, ensure_ascii=False))
                    else:
                        out_lines.append(f"ERROR {e.id} :: {str(ex)}")
                    continue
                adapter = IndexBuilder().adapter
                contracts = list(adapter.parse_file(e.file_path))
                matched = None
                for fc in contracts:
                    if fc.id == e.id:
                        matched = fc
                        break
                if matched is None:
                    if output_format == "jsonl":
                        print(json.dumps({
                            "status": "ERROR",
                            "func_id": e.id,
                            "file_path": e.file_path,
                            "reason": "contract not found"
                        }, ensure_ascii=False))
                    else:
                        out_lines.append(f"ERROR {e.id} :: contract not found")
                    continue
                res = guard.audit(matched, src, provider, file_path=e.file_path)
                if debug:
                    print(f"[DEBUG] Prompt >>>\n{res.prompt or ''}\n[DEBUG] Raw <<<\n{res.raw_output or ''}")
                reason = " ".join((res.reason or "").split())
                llm_called = res.status not in ("CONTRACT_GAP", "SKIPPED_NO_CONTRACT")
                mapped_status = (
                    "OK"
                    if res.status == "OK"
                    else (
                        "POSSIBLE_SEMANTIC_DRIFT"
                        if res.status == "MISMATCH"
                        else (res.status if res.status in ("CONTRACT_GAP", "SKIPPED_NO_CONTRACT") else "ERROR")
                    )
                )
                if output_format == "jsonl":
                    print(json.dumps({
                        "status": mapped_status,
                        "func_id": e.id,
                        "file_path": e.file_path,
                        "provider": provider.name,
                        "model": model,
                        "reason": reason if res.status != "OK" else None,
                        "llm_called": llm_called,
                    }, ensure_ascii=False))
                else:
                    semantic_counts[mapped_status if mapped_status in semantic_counts else "ERROR"] += 1
                    if res.status == "OK":
                        out_lines.append(f"OK {e.id}")
                    elif res.status == "MISMATCH":
                        out_lines.append(f"POSSIBLE_SEMANTIC_DRIFT {e.id} :: {reason}")
                    elif res.status == "CONTRACT_GAP":
                        out_lines.append(f"CONTRACT_GAP {e.id} :: {reason}")
                    elif res.status == "SKIPPED_NO_CONTRACT":
                        out_lines.append(f"SKIPPED_NO_CONTRACT {e.id} :: {reason}")
                    else:
                        out_lines.append(f"ERROR {e.id} :: {reason}")
            if not out_lines:
                if output_format == "plain":
                    print(t("cli.semantic.notargets"))
            else:
                if output_format == "plain":
                    if verbose:
                        for ln in out_lines:
                            print(ln)
                    elif out_lines:
                        print(
                            "summary: "
                            f"OK={semantic_counts['OK']} "
                            f"POSSIBLE_SEMANTIC_DRIFT={semantic_counts['POSSIBLE_SEMANTIC_DRIFT']} "
                            f"CONTRACT_GAP={semantic_counts['CONTRACT_GAP']} "
                            f"SKIPPED_NO_CONTRACT={semantic_counts['SKIPPED_NO_CONTRACT']} "
                            f"ERROR={semantic_counts['ERROR']}"
                        )
        return {
            "bindings": len(bindings),
            "ddt_violations": len(list(getattr(rep, "violations", []) or [])),
            "ddt_baseline_missing": baseline_missing_count,
            "semantic_targets": semantic_targets_count,
            "semantic_counts": semantic_counts,
        }

    def _run_fast_ddt_for_ci():
        scanner = DDTScanner()
        bindings = scanner.scan_tests()
        validator = DDTValidator()
        return validator.validate(bindings)

    def _empty_status_report():
        return type(
            "CheckpointStatusReport",
            (),
            {
                "drift": [],
                "modified": [],
                "contract_changed": [],
                "contract_gap": [],
                "skipped_no_contract": [],
                "contract_parse_error": [],
                "unsupported_syntax_advisory": [],
                "untracked": [],
                "missing": [],
                "counts": {
                    "drift": 0,
                    "modified": 0,
                    "contract_changed": 0,
                    "contract_gap": 0,
                    "skipped_no_contract": 0,
                    "contract_parse_error": 0,
                    "unsupported_syntax_advisory": 0,
                    "untracked": 0,
                    "missing": 0,
                },
            },
        )()

    def _empty_ddt_report():
        return type(
            "CheckpointDDTReport",
            (),
            {"valid": [], "violations": [], "advisory": [], "counts": {"valid": 0, "violations": 0, "advisory": 0}},
        )()

    def _collect_status_records_for_checkpoint_ci(rep):
        records = []
        records.extend(getattr(rep, "drift", []))
        records.extend(getattr(rep, "modified", []))
        records.extend(getattr(rep, "contract_changed", []))
        records.extend(getattr(rep, "contract_gap", []))
        records.extend(getattr(rep, "skipped_no_contract", []))
        records.extend(getattr(rep, "contract_parse_error", []))
        records.extend(getattr(rep, "unsupported_syntax_advisory", []))
        records.extend(getattr(rep, "untracked", []))
        records.extend(getattr(rep, "missing", []))
        return records

    def _collect_changed_modules_from_status(rep):
        return collect_changed_modules_from_status(
            rep,
            repo_root=Path.cwd(),
            indexed_modules=_collect_all_indexed_modules_for_generated_context(),
        )

    def _collect_changed_paths_from_status(rep):
        return collect_changed_paths_from_status(rep)

    def _collect_changed_modules():
        rep = SyncEngine().check_status()
        return _collect_changed_modules_from_status(rep)

    def _collect_all_indexed_modules_for_generated_context():
        try:
            return collect_all_indexed_modules(prefer_fresh_source=True)
        except TypeError:
            return collect_all_indexed_modules()

    def _collect_module_context_for_generated_context(module: str):
        try:
            return collect_module_context(module, prefer_fresh_source=True)
        except TypeError:
            return collect_module_context(module)

    def _to_repo_relative_display(path: Path) -> str:
        try:
            return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except Exception:
            return path.as_posix()

    def _normalize_l2_write_paths(result) -> List[Path]:
        def _is_l2_meta(path_obj: Path) -> bool:
            return path_obj.name == "_meta.json"

        if result is None:
            return []
        if isinstance(result, Path):
            return [] if _is_l2_meta(result) else [result]
        if isinstance(result, (list, tuple)):
            out: List[Path] = []
            for item in result:
                if isinstance(item, Path):
                    if not _is_l2_meta(item):
                        out.append(item)
                else:
                    candidate = Path(str(item))
                    if not _is_l2_meta(candidate):
                        out.append(candidate)
            return out
        candidate = Path(str(result))
        return [] if _is_l2_meta(candidate) else [candidate]

    def _print_log_write_result(entry, mgr: DiaryManager) -> None:
        # Keep the first line as entry JSON for script compatibility.
        print(entry.to_json())
        target = mgr._current_file_path(entry.ts)
        print(t("cli.log.write_target", path=_to_repo_relative_display(target)))
        print(t("cli.log.path_policy"))

    def _render_log_write_error(exc: LogDraftError) -> str:
        message = str(exc)
        if "No latest draft found." in message:
            return t("cli.log.write.latest_missing")
        if "Unsafe --from-draft path" in message:
            return t("cli.log.write.unsafe_draft_path", message=message)
        return t("cli.log.write.from_draft_read_error", message=message)

    def _render_log_message_error(exc: ValueError) -> str:
        message = str(exc)
        if message == "summary is required":
            return t("cli.log.message.summary_required")
        if message == "invalid type":
            return t("cli.log.message.invalid_type", value=str(getattr(args, "type", "") or ""))
        if message == "invalid importance":
            return t("cli.log.message.invalid_importance", value=str(getattr(args, "importance", "") or ""))
        if message == "invalid visibility":
            return t("cli.log.message.invalid_visibility", value=str(getattr(args, "visibility", "") or ""))
        return message

    def _build_log_draft_next_actions_text() -> str:
        return "\n".join(
            [
                t("cli.log.draft.next_actions.header"),
                t("cli.log.draft.next_actions.write"),
                t("cli.log.draft.next_actions.save"),
                t("cli.log.draft.next_actions.write_yes"),
            ]
        )

    def _print_log_write_from_draft_result(result: dict) -> None:
        print(t("cli.log.write.diary_path", path=result["diary_path_display"]))
        print(t("cli.log.write.summary_line", summary=str(result["entry"].get("summary") or "")))
        print(t("cli.log.write.source_line", path=result["source_draft_display"]))
        print(t("cli.log.write.marker_line", path=result["marker_path_display"]))
        for warning in list(result.get("warnings") or []):
            print(
                t(
                    "cli.log.write.marker_warning",
                    marker_path=result["marker_path_display"],
                    message=str(warning),
                ),
                file=sys.stderr,
            )

    def _sanitize_module_for_display(module: str, *, repo_root: Path) -> str:
        raw = str(module or "").strip()
        if not raw:
            return "<outside-repo>"
        normalized = raw.replace("\\", "/")
        is_windows_abs = bool(re.match(r"(?i)^[a-z]:/", normalized)) or normalized.startswith("//")
        candidate = Path(normalized)
        if candidate.is_absolute():
            try:
                rel = candidate.resolve().relative_to(repo_root.resolve()).as_posix()
                return rel
            except Exception:
                base = candidate.name or Path(normalized.rstrip("/")).name
                return f"<outside-repo>/{base}" if base else "<outside-repo>"
        if is_windows_abs:
            marker = f"/{repo_root.name.lower()}/"
            lower = normalized.lower()
            idx = lower.find(marker)
            if idx != -1:
                rel = normalized[idx + len(marker) :].strip("/")
                if rel:
                    return rel
            base = Path(normalized.rstrip("/")).name or Path(normalized).name
            return f"<outside-repo>/{base}" if base else "<outside-repo>"
        return normalized.strip("/") or "<outside-repo>"

    def _classify_module_safety(module: str, *, repo_root: Path) -> Tuple[bool, str, str]:
        raw = str(module or "").strip()
        if not raw:
            return False, t("cli.docs.unsafe_reason.invalid"), ""

        normalized = raw.replace("\\", "/")
        while "//" in normalized:
            normalized = normalized.replace("//", "/")

        # Absolute modules are only valid when they can be mapped back into repo root.
        parts = [part for part in normalized.split("/") if part not in ("", ".")]
        head = parts[0] if parts else ""
        is_windows_abs = bool(re.match(r"(?i)^[a-z]:$", head)) or bool(re.match(r"(?i)^[a-z]:/", normalized))
        is_absolute = normalized.startswith("/") or normalized.startswith("//") or is_windows_abs
        if is_absolute:
            rel = ""
            candidate = Path(normalized)
            if candidate.is_absolute():
                try:
                    rel = candidate.resolve().relative_to(repo_root.resolve()).as_posix()
                except Exception:
                    return False, t("cli.docs.unsafe_reason.outside_root"), ""
            else:
                marker = f"/{repo_root.name.lower()}/"
                lower = normalized.lower()
                idx = lower.find(marker)
                if idx == -1:
                    return False, t("cli.docs.unsafe_reason.outside_root"), ""
                rel = normalized[idx + len(marker) :].strip("/")
            rel_parts = [part for part in rel.split("/") if part not in ("", ".")]
            if not rel_parts or any(part == ".." for part in rel_parts):
                return False, t("cli.docs.unsafe_reason.invalid"), ""
            parts = rel_parts
        else:
            if not parts:
                return False, t("cli.docs.unsafe_reason.invalid"), ""
            if any(part == ".." for part in parts):
                return False, t("cli.docs.unsafe_reason.traversal"), ""

        # Accept file-path candidates by inferring their parent module.
        if parts and (parts[-1] == "__init__.py" or "." in parts[-1]):
            parts = parts[:-1]
        if not parts:
            return False, t("cli.docs.unsafe_reason.invalid"), ""
        if any(part == ".." for part in parts):
            return False, t("cli.docs.unsafe_reason.traversal"), ""
        return True, "", "/".join(parts)

    def _select_safe_modules(modules: List[str], *, strict: bool = False) -> Tuple[List[str], List[Tuple[str, str]]]:
        repo_root = Path.cwd().resolve()
        safe_modules: List[str] = []
        skipped: List[Tuple[str, str]] = []
        seen = set()
        for module in modules:
            is_safe, reason, normalized = _classify_module_safety(module, repo_root=repo_root)
            if is_safe and normalized:
                if normalized not in seen:
                    seen.add(normalized)
                    safe_modules.append(normalized)
                continue
            display = _sanitize_module_for_display(str(module), repo_root=repo_root)
            if strict:
                raise ValueError(t("cli.docs.module_unsafe", module=display, reason=reason))
            skipped.append((display, reason))
        return safe_modules, skipped

    def _print_skipped_unsafe_modules(skipped: List[Tuple[str, str]]) -> None:
        if not skipped:
            return
        print(t("cli.docs.skipped_unsafe.title"))
        for display, reason in skipped:
            print(f"- {display} ({reason})")

    def _finish_self_check_rows(results):
        rows = []
        for summary in results:
            for label, view_result in (
                (t("cli.stale.l2"), summary.l2_readme),
                (t("cli.stale.l2_export"), summary.l2_readme_export),
                (t("cli.stale.capsule"), summary.module_capsule),
            ):
                if view_result.status in ("up_to_date", "disabled"):
                    continue
                rows.append(
                    {
                        "module": summary.module,
                        "view": label,
                        "status": view_result.status,
                        "reason": view_result.reason or view_result.status,
                        "suggested_command": view_result.suggested_command,
                    }
                )
        return rows

    def _print_finish_sync_context_self_check(modules: List[str]) -> bool:
        if not modules:
            print(t("cli.finish.sync_context.self_check.skipped"))
            return True
        results = [check_module_derived_views_stale(module) for module in modules]
        residual = _finish_self_check_rows(results)
        if not residual:
            print(t("cli.finish.sync_context.self_check.pass", count=len(modules)))
            return True

        print(t("cli.finish.sync_context.self_check.residual", count=len(residual)))
        for row in residual:
            print(
                t(
                    "cli.finish.sync_context.self_check.item",
                    module=row["module"],
                    view=row["view"],
                    status=row["status"],
                    reason=row["reason"],
                )
            )

        commands = []
        seen = set()
        for row in residual:
            command = str(row.get("suggested_command") or "").strip()
            if not command or command in seen:
                continue
            seen.add(command)
            commands.append(command)
        if commands:
            print(t("cli.finish.sync_context.self_check.guidance"))
            for command in commands:
                print(f"  - {command}")
        return False

    def _print_finish_sync_context_advisory(changed_paths: List[str]) -> None:
        advisory_paths = detect_generator_integrity_changes(changed_paths, repo_root=Path.cwd())
        if not advisory_paths:
            return
        print("")
        print(t("cli.finish.sync_context.advisory.title"))
        for path in advisory_paths:
            print(f"- {path}")
        print(t("cli.finish.sync_context.advisory.body"))
        print("  - harbor docs --all --write")
        print("  - harbor module seal --all --write")

    def _run_docs_changed(*, write=False, force=False, modules=None):
        gen = L2Generator(prefer_fresh_source=True)
        raw_modules = modules if modules is not None else _collect_changed_modules()
        target_modules, skipped = _select_safe_modules(list(raw_modules), strict=False)
        _print_skipped_unsafe_modules(skipped)
        if not target_modules:
            print(t("cli.docs.changed.none"))
            return []
        print(t("cli.docs.changed.found"))
        for module in target_modules:
            print(f"- {module}")
        if not write:
            print("")
            print(t("cli.docs.preview_only"))
        updated = []
        for module in target_modules:
            md = gen.generate(module)
            if write:
                targets = _normalize_l2_write_paths(gen.write(module, md, force=force))
                updated.extend(targets)
            else:
                print("")
                print(md)
        if write:
            if not updated:
                print(t("cli.docs.nochanges"))
            else:
                print("")
                print(t("cli.docs.updated"))
                for path in updated:
                    print(f"- {_to_repo_relative_display(path)}")
        return target_modules

    def _run_module_seal_changed(*, write=False, modules=None):
        target_modules = modules if modules is not None else _collect_changed_modules()
        if not target_modules:
            print(t("cli.module.seal.changed.none"))
            return []
        print(t("cli.module.seal.changed.found"))
        for module in target_modules:
            print(f"- {module}")

        valid_contexts = []
        for module in target_modules:
            context = _collect_module_context_for_generated_context(module)
            if context.get("key_files") or context.get("contracts"):
                valid_contexts.append(context)

        if not valid_contexts:
            print(t("cli.module.seal.changed.none"))
            return target_modules

        if not write:
            print("")
            first_target = resolve_module_capsule_paths(valid_contexts[0].get("module", ""), root=Path.cwd()).get("canonical_dir")
            preview_path = _to_repo_relative_display(first_target) if first_target is not None else ".harbor/views/modules/<module>"
            print(t("cli.module.seal.batch.preview_only", path=preview_path))
            for context in valid_contexts:
                module_name = context.get("module", "")
                previews = preview_module_capsule(context)
                print("")
                print(t("cli.module.seal.title", module=module_name))
                for name in ["module-card.md", "review-checklist.md", "debug-playbook.md"]:
                    print("")
                    print(f"--- {name} ---")
                    print(previews[name])
            return target_modules

        updated = []
        for context in valid_contexts:
            result = write_module_capsule(context)
            updated.extend(result.canonical_paths)
            updated.extend(result.exported_paths)
        print(t("cli.module.seal.batch.updated"))
        for path in updated:
            print(f"- {_to_repo_relative_display(path)}")
        return target_modules

    def _run_module_stale_changed(*, modules=None):
        target_modules = modules if modules is not None else _collect_changed_modules()
        if not target_modules:
            print(t("cli.module.stale.none_changed"))
            return []
        print(t("cli.module.stale.changed.found"))
        for module in target_modules:
            context = _collect_module_context_for_generated_context(module)
            result = check_module_capsule_stale(context)
            status_text = t("cli.module.stale.up_to_date") if result.get("status") == "up_to_date" else t(
                "cli.module.stale.stale"
            )
            print(f"- {module}: {status_text}")
        return target_modules

    def _coerce_report_items(payload_obj, key: str):
        items = payload_obj.get(key, [])
        return items if isinstance(items, list) else []

    def _load_json_report(report_path: Path) -> dict:
        raw = report_path.read_bytes()
        decode_errors = []
        for encoding in ("utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be"):
            try:
                text = raw.decode(encoding)
            except Exception as ex:
                decode_errors.append(f"{encoding}: {str(ex)}")
                continue
            try:
                payload_obj = json.loads(text)
            except Exception as ex:
                decode_errors.append(f"{encoding}: {str(ex)}")
                continue
            if not isinstance(payload_obj, dict):
                raise ValueError("report JSON root must be an object.")
            return payload_obj
        raise ValueError("failed to parse report JSON: " + "; ".join(decode_errors))

    def _normalize_next_item(source_command: str, raw_item: dict, *, blocking: bool, include_guidance: bool) -> dict:
        item = dict(raw_item or {})
        normalized = {
            "category": str(item.get("category") or item.get("kind") or "unknown"),
            "func_id": item.get("func_id"),
            "file_path": item.get("file_path"),
            "reason": item.get("reason"),
            "target_id": item.get("target_id"),
            "language": item.get("language"),
            "symbol_kind": item.get("symbol_kind"),
            "adapter": item.get("adapter"),
            "export_mode": item.get("export_mode"),
            "public_surface_evidence": item.get("public_surface_evidence"),
            "data_contract_kind": item.get("data_contract_kind"),
            "schema_source_kind": item.get("schema_source_kind"),
            "source_confidence_summary": item.get("source_confidence_summary"),
            "contract_source_kinds": item.get("contract_source_kinds"),
            "contract_source_fingerprints": item.get("contract_source_fingerprints"),
            "blocking": bool(blocking),
        }
        if include_guidance:
            existing = item.get("guidance")
            if isinstance(existing, dict):
                guidance_payload = existing
            elif source_command == "checkpoint":
                guidance_payload = guidance_for_checkpoint_category(
                    str(item.get("category") or "unknown"),
                    language=str(item.get("language") or ""),
                ).to_dict()
            elif source_command == "stale":
                generated = guidance_for_stale_item(
                    kind=item.get("kind"),
                    view=item.get("view"),
                    status=item.get("status"),
                )
                guidance_payload = (
                    generated.to_dict()
                    if generated is not None
                    else generic_conservative_guidance(
                        what_happened="Stale report item is unknown or missing explicit deterministic mapping."
                    ).to_dict()
                )
            elif source_command == "doctor":
                generated = guidance_for_doctor_item(
                    check=item.get("check"),
                    status=str(item.get("status") or "").lower(),
                )
                guidance_payload = (
                    generated.to_dict()
                    if generated is not None
                    else generic_conservative_guidance(
                        what_happened="Doctor report item is unknown or missing explicit deterministic mapping."
                    ).to_dict()
                )
            else:
                guidance_payload = generic_conservative_guidance(
                    what_happened="Report source is unknown; using conservative fallback guidance."
                ).to_dict()
            normalized["guidance"] = guidance_payload
        return normalized

    def _render_next_text(source_command: str, items: List[dict]) -> str:
        lines: List[str] = ["Harbor Next Actions", ""]
        blocking_items = [row for row in items if row.get("blocking")]
        advisory_items = [row for row in items if not row.get("blocking")]

        def _append_group(title: str, group_items: List[dict]) -> None:
            if not group_items:
                return
            lines.append(f"{title}:")
            for idx, row in enumerate(group_items, start=1):
                lines.append(f"{idx}. {row.get('category', 'unknown')}")
                target = row.get("func_id") or row.get("file_path")
                if target:
                    lines.append(f"   Target: {target}")
                if row.get("reason"):
                    lines.append(f"   Reason: {row.get('reason')}")
                context_bits = []
                if row.get("language"):
                    context_bits.append(f"language={row.get('language')}")
                if row.get("symbol_kind"):
                    context_bits.append(f"symbol_kind={row.get('symbol_kind')}")
                if row.get("export_mode"):
                    context_bits.append(f"export_mode={row.get('export_mode')}")
                if row.get("data_contract_kind"):
                    context_bits.append(f"data_contract_kind={row.get('data_contract_kind')}")
                if row.get("schema_source_kind"):
                    context_bits.append(f"schema_source_kind={row.get('schema_source_kind')}")
                if row.get("source_confidence_summary"):
                    context_bits.append(
                        f"source_confidence_summary={row.get('source_confidence_summary')}"
                    )
                if context_bits:
                    lines.append(f"   Context: {', '.join(context_bits)}")
                guidance = row.get("guidance")
                if isinstance(guidance, dict):
                    lines.append(f"   What happened: {guidance.get('what_happened', '')}")
                    lines.append(f"   Recommended action: {guidance.get('recommended_action', '')}")
                    if guidance.get("anti_action"):
                        lines.append(f"   Do not: {guidance.get('anti_action')}")
                    lines.append(f"   Requires user decision: {guidance.get('decision_required', True)}")
            lines.append("")

        _append_group("Blocking failures", blocking_items)
        _append_group("Advisory", advisory_items)
        if not blocking_items and not advisory_items:
            lines.append(f"No actionable items from source command: {source_command}")
        return "\n".join(lines).rstrip()

    if args.command == "lock":
        code_roots = args.code_root
        cache_dir = Path(args.cache_dir) if args.cache_dir else None
        lock_summary = _run_lock(
            code_roots=code_roots,
            cache_dir=cache_dir,
            no_incremental=getattr(args, "no_incremental", False),
            no_register_adopted=getattr(args, "no_register_adopted", False),
            register_scan=getattr(args, "register_scan", False),
        )
    elif args.command == "accept":
        accept_summary = _run_accept(
            output_path=getattr(args, "output", None),
            no_cache_refresh=bool(getattr(args, "no_cache_refresh", False)),
        )
        if getattr(args, "format", "text") == "json":
            _emit_json_stdout(accept_summary)
        else:
            print(t("cli.accept.done"))
            print(t("cli.accept.artifact_path", path=accept_summary["artifact_path"]))
            print(t("cli.accept.artifact_items", count=accept_summary["artifact_items"]))
            print(t("cli.accept.cache_refreshed", value=str(accept_summary["cache_refreshed"]).lower()))
        _write_change_window_snapshot_safe(
            "accept",
            summary=accept_summary,
            validation={
                "command": "accept",
                "success": True,
                "artifact_written": True,
                "artifact_path": accept_summary["artifact_path"],
                "artifact_items": accept_summary["artifact_items"],
                "cache_refreshed": accept_summary["cache_refreshed"],
            },
        )
    elif args.command == "start":
        print(t("cli.start.title"))
        _, clean = _run_status(verbose=False)
        if clean:
            print(t("cli.start.clean"))
        else:
            print(t("cli.start.dirty"))
    elif args.command == "checkpoint":
        if not getattr(args, "ci", False) and getattr(args, "format", "text") != "text":
            parser.error(t("cli.checkpoint.error.format_ci_only"))
        if not getattr(args, "ci", False):
            print(t("cli.checkpoint.title"))
            rep, clean = _run_status(verbose=False)
            if not clean:
                _print_checkpoint_contract_impact(rep)
            check_summary = _run_check(fast=True, verbose=False)
            _write_change_window_snapshot_safe(
                "checkpoint",
                summary=_build_checkpoint_snapshot_summary(
                    status_report=rep,
                    check_summary=check_summary,
                ),
                validation={
                    "command": "checkpoint",
                    "ci": False,
                    "status_counts": dict(getattr(rep, "counts", {}) or {}),
                    "check": dict(check_summary),
                },
            )
        else:
            advice_settings = resolve_advice_settings(cli_advice=getattr(args, "advice", None), repo_root=Path.cwd())
            check_errors = []
            status_report = _empty_status_report()
            ddt_report = _empty_ddt_report()
            records = []
            baseline_source = "accepted_artifact"
            baseline_path = _repo_display_path(Path.cwd() / ACCEPTED_CHECKPOINT_BASELINE_PATH)
            baseline_found = False
            baseline_error_category = None
            baseline_error_reason = None
            try:
                baseline_payload = load_checkpoint_baseline_artifact()
                baseline_found = True
                status_report = SyncEngine().check_status(
                    baseline_snapshot=baseline_payload,
                    baseline_source=baseline_source,
                )
                records = _collect_status_records_for_checkpoint_ci(status_report)
            except AcceptedBaselineMissingError:
                baseline_error_category = "accepted_baseline_missing"
                baseline_error_reason = t("cli.ci.checkpoint.failure.accepted_baseline_missing")
            except AcceptedBaselineInvalidError:
                baseline_error_category = "accepted_baseline_invalid"
                baseline_error_reason = t("cli.ci.checkpoint.failure.accepted_baseline_invalid")
            except Exception as ex:
                check_errors.append(f"status_check_failed: {str(ex)}")
            try:
                ddt_report = _run_fast_ddt_for_ci()
            except Exception as ex:
                check_errors.append(f"ddt_check_failed: {str(ex)}")
            try:
                contract_impact_report = build_contract_impact_report(records)
            except Exception as ex:
                check_errors.append(f"contract_impact_failed: {str(ex)}")
                contract_impact_report = build_contract_impact_report([])
            ci_result = build_checkpoint_ci_result(
                status_report=status_report,
                ddt_report=ddt_report,
                contract_impact_report=contract_impact_report,
                check_errors=check_errors,
                advice_settings=advice_settings,
                baseline_source=baseline_source,
                baseline_path=baseline_path,
                baseline_found=baseline_found,
                baseline_error_category=baseline_error_category,
                baseline_error_reason=baseline_error_reason,
            )
            if args.format == "json":
                _emit_json_stdout(checkpoint_ci_result_to_dict(ci_result))
            else:
                print(format_checkpoint_ci_result(ci_result))
            _write_change_window_snapshot_safe(
                "checkpoint",
                summary=_build_checkpoint_snapshot_summary(
                    status_report=status_report,
                    check_summary={
                        "ddt_violations": len(list(getattr(ddt_report, "violations", []) or [])),
                        "ddt_advisory": len(list(getattr(ddt_report, "advisory", []) or [])),
                    },
                    ci_result=ci_result,
                ),
                validation={
                    "command": "checkpoint",
                    "ci": True,
                    "format": args.format,
                    "exit_code": int(getattr(ci_result, "exit_code", 0)),
                    "status": getattr(ci_result, "status", None),
                    "check_errors": list(check_errors),
                    "ci_failures": len(list(getattr(ci_result, "ci_failures", []) or [])),
                    "advisory": len(list(getattr(ci_result, "advisory", []) or [])),
                },
            )
            if ci_result.exit_code != 0:
                raise SystemExit(ci_result.exit_code)
    elif args.command == "next":
        report_path = Path(str(getattr(args, "from_path", "") or "")).resolve()
        if not report_path.exists() or not report_path.is_file():
            parser.error("--from must point to an existing JSON report file.")
        try:
            payload = _load_json_report(report_path)
        except Exception as ex:
            parser.error(str(ex))

        source_command = str(payload.get("command") or "unknown")
        advice_settings = resolve_advice_settings(cli_advice=getattr(args, "advice", None), repo_root=Path.cwd())
        include_guidance = advice_settings.mode == "basic"

        items: List[dict] = []
        for row in _coerce_report_items(payload, "ci_failures"):
            if not isinstance(row, dict):
                continue
            items.append(_normalize_next_item(source_command, row, blocking=True, include_guidance=include_guidance))
        for row in _coerce_report_items(payload, "advisory"):
            if not isinstance(row, dict):
                continue
            items.append(_normalize_next_item(source_command, row, blocking=False, include_guidance=include_guidance))

        max_items = max(int(getattr(args, "max_items", 20) or 20), 1)
        items = items[:max_items]

        if args.format == "json":
            out = {
                "command": "next",
                "source_command": source_command,
                "status": "ok",
                "items": items,
                "writes_files": False,
                "llm_used": False,
            }
            _emit_json_stdout(out)
        else:
            print(_render_next_text(source_command, items))
    elif args.command == "finish":
        print(t("cli.finish.title"))
        status_report, _ = _run_status(verbose=getattr(args, "verbose", False))
        check_summary = _run_check(fast=False, output_format="plain", verbose=getattr(args, "verbose", False))
        blocking_count = (
            len(list(getattr(status_report, "drift", []) or []))
            + len(list(getattr(status_report, "modified", []) or []))
            + len(list(getattr(status_report, "contract_changed", []) or []))
            + len(list(getattr(status_report, "contract_gap", []) or []))
            + len(list(getattr(status_report, "contract_parse_error", []) or []))
            + len(list(getattr(status_report, "untracked", []) or []))
            + len(list(getattr(status_report, "missing", []) or []))
            + int(check_summary.get("ddt_violations", 0))
        )
        print("")
        print(t("cli.finish.summary.title"))
        print(
            t(
                "cli.finish.summary.blocking",
                status=t("cli.finish.summary.status.yes") if blocking_count > 0 else t("cli.finish.summary.status.no"),
            )
        )
        print(
            t(
                "cli.finish.summary.ddt_binding",
                status=t("cli.finish.summary.status.ok")
                if int(check_summary.get("ddt_violations", 0)) == 0
                else t("cli.finish.summary.status.fail"),
            )
        )
        print(
            t(
                "cli.finish.summary.ddt_advisory",
                count=int(check_summary.get("ddt_baseline_missing", 0)),
            )
        )
        print(
            t(
                "cli.finish.summary.semantic_targets",
                count=int(check_summary.get("semantic_targets", 0)),
            )
        )
        if not getattr(args, "sync_context", False):
            print(t("cli.finish.next_steps"))
        else:
            print("")
            print(t("cli.finish.sync_context.title"))
            changed_paths = _collect_changed_paths_from_status(status_report)
            changed_modules = _collect_changed_modules_from_status(status_report)
            if not changed_modules:
                print(t("cli.finish.sync_context.none"))
            else:
                print(t("cli.finish.sync_context.docs"))
                _run_docs_changed(write=True, modules=changed_modules)
                print("")
                print(t("cli.finish.sync_context.capsules"))
                _run_module_seal_changed(write=True, modules=changed_modules)
                print("")
                print(t("cli.finish.sync_context.stale"))
                _print_finish_sync_context_self_check(changed_modules)
            _print_finish_sync_context_advisory(changed_paths)
            print("")
            print(t("cli.finish.sync_context.next_steps"))
        _write_change_window_snapshot_safe(
            "finish",
            summary={
                "sync_context": bool(getattr(args, "sync_context", False)),
                "blocking": blocking_count > 0,
                "blocking_count": blocking_count,
                "check": dict(check_summary),
            },
            validation={
                "command": "finish",
                "sync_context": bool(getattr(args, "sync_context", False)),
                "status_counts": dict(getattr(status_report, "counts", {}) or {}),
                "check": dict(check_summary),
            },
        )
    elif args.command == "config" and args.cfg_cmd == "list":
        data = _load_cfg_data_safe()
        code_roots = data.get("code_roots", ["harbor/**"])
        exclude_paths = data.get("exclude_paths", [])
        profile = data.get("profile", "enforce_l3")
        language = str(data.get("language", "auto"))
        adopted_roots = data.get("adopted_roots", [])
        table = Table(title=t("cli.config.title"))
        table.add_column(t("cli.config.key"), style="bold")
        table.add_column(t("cli.config.value"))
        table.add_row("profile", profile)
        table.add_row("code_roots", ", ".join(code_roots))
        table.add_row("exclude_paths", ", ".join(exclude_paths))
        table.add_row("adopted_roots", ", ".join(adopted_roots))
        table.add_row("language", language or "auto")
        Console().print(table)
        if code_roots == ["**/*.py"]:
            print(t("cli.config.adopt_hint"))
    elif args.command == "config" and args.cfg_cmd == "add":
        data = _load_cfg_data_safe()
        roots = data.get("code_roots", [])
        p = args.path
        if p not in roots:
            roots.append(p)
        data["code_roots"] = roots
        data.setdefault("exclude_paths", [])
        data.setdefault("profile", data.get("profile", "enforce_l3"))
        data.setdefault("language", data.get("language", "auto"))
        data.setdefault("adopted_roots", [])
        _write_cfg_data(data)
        print(t("cli.config.added", path=p))
    elif args.command == "config" and args.cfg_cmd == "remove":
        data = _load_cfg_data_safe()
        roots = data.get("code_roots", [])
        p = args.path
        if p in roots:
            roots = [x for x in roots if x != p]
            data["code_roots"] = roots
            adopted = data.get("adopted_roots", [])
            if p in adopted:
                adopted = [x for x in adopted if x != p]
                data["adopted_roots"] = adopted
            _write_cfg_data(data)
            print(t("cli.config.removed", path=p))
        else:
            print(t("cli.config.nochanges"))
    elif args.command == "config" and args.cfg_cmd == "adopted":
        data = _load_cfg_data_safe()
        excludes = data.get("exclude_paths", [])
        db = IndexBuilder().db
        files = [fp for fp, _ in db.get_all_files()]
        from harbor.core.utils import derive_adopted_roots
        derived = derive_adopted_roots(files, exclude_patterns=excludes, min_count=getattr(args, "min_count", 1))
        table = Table(title=t("cli.config.title"))
        table.add_column(t("cli.config.key"), style="bold")
        table.add_column(t("cli.config.value"))
        table.add_row("derived_adopted_roots", ", ".join(derived))
        Console().print(table)
        if getattr(args, "write", False):
            adopted = data.get("adopted_roots", [])
            for p in derived:
                if p not in adopted:
                    adopted.append(p)
                if p not in data.get("code_roots", []):
                    data["code_roots"] = data.get("code_roots", []) + [p]
            data["adopted_roots"] = adopted
            _write_cfg_data(data)
            print(t("cli.config.adopted.wrote", count=len(derived)))
    elif args.command == "status":
        _run_status(verbose=getattr(args, "verbose", False))
    elif args.command == "check":
        _run_check(
            fast=args.fast,
            module=args.module,
            func=args.func,
            diff_only=args.diff_only,
            debug=args.debug,
            output_format=args.format,
            verbose=getattr(args, "verbose", False),
        )
    elif args.command == "docs":
        docs_mode_count = int(bool(args.module)) + int(bool(args.changed)) + int(bool(args.all_modules))
        if docs_mode_count != 1:
            parser.error(t("cli.docs.mode_conflict"))
        gen = L2Generator(prefer_fresh_source=True)
        if args.module:
            module_name = args.module
            if args.write:
                selected, _ = _select_safe_modules([args.module], strict=True)
                module_name = selected[0]
            md = gen.generate(module_name)
            if args.write:
                targets = _normalize_l2_write_paths(gen.write(module_name, md, force=args.force))
                if not targets:
                    print(t("cli.docs.nochanges"))
                else:
                    print(t("cli.docs.updated"))
                    for path in targets:
                        print(f"- {_to_repo_relative_display(path)}")
            else:
                print(md)
        else:
            if args.changed:
                _run_docs_changed(write=args.write, force=args.force)
                return
            else:
                raw_modules = _collect_all_indexed_modules_for_generated_context()
                modules, skipped = _select_safe_modules(raw_modules, strict=False)
                _print_skipped_unsafe_modules(skipped)
                if not modules:
                    print(t("cli.docs.all.none"))
                    return
                print(t("cli.docs.all.found"))
            for module in modules:
                print(f"- {module}")
            if not args.write:
                print("")
                print(t("cli.docs.preview_only"))
            updated = []
            for module in modules:
                md = gen.generate(module)
                if args.write:
                    targets = _normalize_l2_write_paths(gen.write(module, md, force=args.force))
                    updated.extend(targets)
                else:
                    print("")
                    print(md)
            if args.write:
                if not updated:
                    print(t("cli.docs.nochanges"))
                else:
                    print("")
                    print(t("cli.docs.updated"))
                    for path in updated:
                        print(f"- {_to_repo_relative_display(path)}")
    elif args.command == "stale":
        mode_count = int(bool(args.module)) + int(bool(args.changed)) + int(bool(args.all_modules))
        if mode_count > 1:
            parser.error(t("cli.stale.mode_conflict"))

        scope_text = t("cli.stale.scope.changed")
        scope_value = "changed"
        if args.module:
            modules = [args.module]
            scope_text = t("cli.stale.scope.module", module=args.module)
            scope_value = f"module:{args.module}"
        elif args.all_modules:
            modules = _collect_all_indexed_modules_for_generated_context()
            scope_text = t("cli.stale.scope.all")
            scope_value = "all"
            if not modules:
                if args.ci:
                    advice_settings = resolve_advice_settings(cli_advice=getattr(args, "advice", None), repo_root=Path.cwd())
                    ci_result = build_stale_ci_result([], scope=scope_value, advice_settings=advice_settings)
                    if args.format == "json":
                        _emit_json_stdout(ci_result_to_dict(ci_result))
                    else:
                        print(format_ci_result(ci_result))
                elif args.format == "json":
                    _emit_json_stdout(stale_report_to_dict([], scope=scope_value))
                else:
                    print(t("cli.stale.none_all"))
                return
        else:
            modules = _collect_changed_modules()
            if not modules:
                if args.ci:
                    advice_settings = resolve_advice_settings(cli_advice=getattr(args, "advice", None), repo_root=Path.cwd())
                    ci_result = build_stale_ci_result([], scope=scope_value, advice_settings=advice_settings)
                    if args.format == "json":
                        _emit_json_stdout(ci_result_to_dict(ci_result))
                    else:
                        print(format_ci_result(ci_result))
                elif args.format == "json":
                    _emit_json_stdout(stale_report_to_dict([], scope=scope_value))
                else:
                    print(t("cli.stale.none_changed"))
                return

        results = [check_module_derived_views_stale(module) for module in modules]
        if args.ci:
            advice_settings = resolve_advice_settings(cli_advice=getattr(args, "advice", None), repo_root=Path.cwd())
            ci_result = build_stale_ci_result(results, scope=scope_value, advice_settings=advice_settings)
            payload = ci_result_to_dict(ci_result)
            if args.format == "json":
                _emit_json_stdout(payload)
            else:
                print(format_ci_result(ci_result))
            if ci_result.exit_code != 0:
                raise SystemExit(ci_result.exit_code)
        elif args.format == "json":
            payload = stale_report_to_dict(results, scope=scope_value)
            _emit_json_stdout(payload)
        else:
            print(format_stale_summary(results, scope_text=scope_text))
    elif args.command == "doctor":
        mode_count = int(bool(args.module)) + int(bool(args.changed)) + int(bool(args.all_modules))
        if mode_count > 1:
            parser.error(t("cli.doctor.mutually_exclusive"))

        scope_text = t("cli.doctor.scope.changed")
        scope_value = "changed"
        if args.module:
            modules = [args.module]
            scope_text = t("cli.doctor.scope.module", module=args.module)
            scope_value = f"module:{args.module}"
        elif args.all_modules:
            modules = _collect_all_indexed_modules_for_generated_context()
            scope_text = t("cli.doctor.scope.all")
            scope_value = "all"
        else:
            modules = _collect_changed_modules()

        report = build_doctor_report(
            scope=scope_text,
            modules=sorted(modules) if args.format == "json" else modules,
        )
        if args.ci:
            advice_settings = resolve_advice_settings(cli_advice=getattr(args, "advice", None), repo_root=Path.cwd())
            ci_result = build_doctor_ci_result(report, advice_settings=advice_settings)
            payload = ci_result_to_dict(ci_result)
            if args.format == "json":
                _emit_json_stdout(payload)
            else:
                print(format_ci_result(ci_result))
            if ci_result.exit_code != 0:
                raise SystemExit(ci_result.exit_code)
        elif args.format == "json":
            payload = report.to_dict(command="doctor")
            payload["scope"] = scope_value
            _emit_json_stdout(payload)
        else:
            print(format_doctor_report(report))
    elif args.command == "verify-generated":
        mode_count = int(bool(args.module)) + int(bool(args.changed)) + int(bool(args.all_modules))
        if mode_count > 1:
            parser.error(t("cli.verify_generated.mode_conflict"))

        scope_text = t("cli.verify_generated.scope.changed")
        scope_value = "changed"
        if args.module:
            modules = [args.module]
            scope_text = t("cli.verify_generated.scope.module", module=args.module)
            scope_value = f"module:{args.module}"
        elif args.all_modules:
            modules = _collect_all_indexed_modules_for_generated_context()
            scope_text = t("cli.verify_generated.scope.all")
            scope_value = "all"
            if not modules:
                report = build_generated_verification_report(scope=scope_value, modules=[])
                if args.ci:
                    advice_settings = resolve_advice_settings(cli_advice=getattr(args, "advice", None), repo_root=Path.cwd())
                    ci_result = build_generated_verification_ci_result(report, advice_settings=advice_settings)
                    if args.format == "json":
                        _emit_json_stdout(ci_result_to_dict(ci_result))
                    else:
                        print(format_ci_result(ci_result))
                elif args.format == "json":
                    _emit_json_stdout(generated_verification_report_to_dict(report))
                else:
                    print(t("cli.verify_generated.none_all"))
                return
        else:
            modules = _collect_changed_modules()
            if not modules:
                report = build_generated_verification_report(scope=scope_value, modules=[])
                if args.ci:
                    advice_settings = resolve_advice_settings(cli_advice=getattr(args, "advice", None), repo_root=Path.cwd())
                    ci_result = build_generated_verification_ci_result(report, advice_settings=advice_settings)
                    if args.format == "json":
                        _emit_json_stdout(ci_result_to_dict(ci_result))
                    else:
                        print(format_ci_result(ci_result))
                elif args.format == "json":
                    _emit_json_stdout(generated_verification_report_to_dict(report))
                else:
                    print(t("cli.verify_generated.none_changed"))
                return

        report = build_generated_verification_report(scope=scope_value, modules=modules)
        if args.ci:
            advice_settings = resolve_advice_settings(cli_advice=getattr(args, "advice", None), repo_root=Path.cwd())
            ci_result = build_generated_verification_ci_result(report, advice_settings=advice_settings)
            if args.format == "json":
                _emit_json_stdout(ci_result_to_dict(ci_result))
            else:
                print(format_ci_result(ci_result))
            if ci_result.exit_code != 0:
                raise SystemExit(ci_result.exit_code)
        elif args.format == "json":
            _emit_json_stdout(generated_verification_report_to_dict(report))
        else:
            print(format_generated_verification_report(report, scope_text=scope_text))
    elif args.command == "workspace" and args.workspace_cmd == "inspect":
        report = build_workspace_inspect_report(Path.cwd())
        if args.format == "json":
            payload = workspace_inspect_report_to_dict(report)
            _emit_json_stdout(payload)
        else:
            print(format_workspace_inspect_report(report))
    elif args.command == "workspace" and args.workspace_cmd == "migrate":
        if not getattr(args, "dry_run", False):
            parser.error(t("cli.workspace.migrate.error.only_dry_run"))
        report = build_workspace_migrate_dry_run_report(Path.cwd())
        if args.format == "json":
            payload = workspace_migrate_report_to_dict(report)
            _emit_json_stdout(payload)
        else:
            print(format_workspace_migrate_report(report))
    elif args.command == "module" and args.module_cmd == "inspect":
        context = collect_module_context(args.module)
        module_name = context.get("module", "")
        if not module_name:
            print(t("cli.module.inspect.none", module=args.module))
            return
        print(t("cli.module.inspect.title", module=module_name))
        if not context.get("key_files") and not context.get("contracts"):
            print(t("cli.module.inspect.none", module=module_name))
            return
        print(f"Module: {module_name}")
        print(f"Strictness: {context.get('strictness', 'standard')}")
        print("Key files:")
        for fp in context.get("key_files", []):
            print(f"- {fp}")
        print("")
        print("Indexed contracts:")
        contracts = context.get("contracts", [])
        if not contracts:
            print("- No indexed contracts found for this module.")
        else:
            for c in contracts:
                print(f"- {c.get('symbol')}")
        print("")
        print("Tests:")
        tests = context.get("tests", [])
        if not tests:
            print("- No test files detected by Harbor.")
        else:
            for tpath in tests:
                print(f"- {tpath}")
    elif args.command == "module" and args.module_cmd == "seal":
        mode_count = int(bool(args.module)) + int(bool(args.changed)) + int(bool(args.all_modules))
        if mode_count != 1:
            parser.error(t("cli.module.seal.mode_conflict"))

        if args.module:
            context = _collect_module_context_for_generated_context(args.module)
            module_name = context.get("module", "")
            if not module_name:
                print(t("cli.module.seal.none", module=args.module))
                return
            if not context.get("key_files") and not context.get("contracts"):
                print(t("cli.module.seal.none", module=module_name))
                return
            print(t("cli.module.seal.title", module=module_name))
            previews = preview_module_capsule(context)
            if not args.write:
                resolved = resolve_module_capsule_paths(module_name, root=Path.cwd()).get("canonical_dir")
                preview_path = _to_repo_relative_display(resolved) if resolved is not None else ".harbor/views/modules/<module>"
                print(t("cli.module.seal.preview_only", path=preview_path))
                for name in ["module-card.md", "review-checklist.md", "debug-playbook.md"]:
                    print("")
                    print(f"--- {name} ---")
                    print(previews[name])
            else:
                result = write_module_capsule(context)
                updated = list(result.canonical_paths) + list(result.exported_paths)
                print(t("cli.module.seal.updated"))
                for path in updated:
                    print(f"- {_to_repo_relative_display(path)}")
            return

        if args.changed:
            _run_module_seal_changed(write=args.write)
            return
        else:
            modules = _collect_all_indexed_modules_for_generated_context()
            if not modules:
                print(t("cli.module.seal.all.none"))
                return
            print(t("cli.module.seal.all.found"))

        for module in modules:
            print(f"- {module}")

        valid_contexts = []
        for module in modules:
            context = _collect_module_context_for_generated_context(module)
            if context.get("key_files") or context.get("contracts"):
                valid_contexts.append(context)

        if not valid_contexts:
            if args.changed:
                print(t("cli.module.seal.changed.none"))
            else:
                print(t("cli.module.seal.all.none"))
            return

        if not args.write:
            print("")
            first_target = resolve_module_capsule_paths(valid_contexts[0].get("module", ""), root=Path.cwd()).get("canonical_dir")
            preview_path = _to_repo_relative_display(first_target) if first_target is not None else ".harbor/views/modules/<module>"
            print(t("cli.module.seal.batch.preview_only", path=preview_path))
            for context in valid_contexts:
                module_name = context.get("module", "")
                previews = preview_module_capsule(context)
                print("")
                print(t("cli.module.seal.title", module=module_name))
                for name in ["module-card.md", "review-checklist.md", "debug-playbook.md"]:
                    print("")
                    print(f"--- {name} ---")
                    print(previews[name])
            return

        updated = []
        for context in valid_contexts:
            result = write_module_capsule(context)
            updated.extend(result.canonical_paths)
            updated.extend(result.exported_paths)
        print(t("cli.module.seal.batch.updated"))
        for path in updated:
            print(f"- {_to_repo_relative_display(path)}")
    elif args.command == "module" and args.module_cmd == "stale":
        mode_count = int(bool(args.module)) + int(bool(args.changed)) + int(bool(args.all_modules))
        if mode_count != 1:
            parser.error(t("cli.module.stale.mode_conflict"))

        if args.module:
            context = _collect_module_context_for_generated_context(args.module)
            module_name = context.get("module", "") or args.module
            result = check_module_capsule_stale(context)
            print(t("cli.module.stale.title", module=module_name))
            if result.get("status") == "up_to_date":
                print(f"- {t('cli.module.stale.status')}: {t('cli.module.stale.up_to_date')}")
                print(f"- {t('cli.module.stale.fingerprint')}: {result.get('current_fingerprint', '')}")
            else:
                print(f"- {t('cli.module.stale.status')}: {t('cli.module.stale.stale')}")
                print(f"- {t('cli.module.stale.reason')}: {result.get('reason', '')}")
                if result.get("reason") != "no indexed records found for module":
                    print(f"- {t('cli.module.stale.suggest')}:")
                    print(f"  harbor module seal {module_name} --write")
            return

        if args.changed:
            _run_module_stale_changed()
            return
        else:
            modules = _collect_all_indexed_modules_for_generated_context()
            if not modules:
                print(t("cli.module.stale.none_all"))
                return
            print(t("cli.module.stale.all.found"))

        for module in modules:
            context = _collect_module_context_for_generated_context(module)
            result = check_module_capsule_stale(context)
            status_text = t("cli.module.stale.up_to_date") if result.get("status") == "up_to_date" else t(
                "cli.module.stale.stale"
            )
            print(f"- {module}: {status_text}")
    elif args.command == "module" and args.module_cmd == "promote-skill":
        context = collect_module_context(args.module)
        check = check_capsule_ready_for_skill(args.module, context=context)
        module_name = check.get("module", "") or args.module
        status = check.get("status")

        if status == "unknown_module":
            print(t("cli.module.promote_skill.unknown_module", module=module_name))
            print(t("cli.module.promote_skill.unknown_module.hint", module=module_name))
            return
        if status == "missing_capsule":
            print(t("cli.module.promote_skill.missing_capsule", module=module_name))
            print(t("cli.module.promote_skill.seal_hint", module=module_name))
            return
        if status == "stale_capsule":
            print(t("cli.module.promote_skill.stale_capsule", module=module_name))
            print(t("cli.module.promote_skill.stale_hint", module=module_name))
            return

        target = write_module_skill(module_name)
        print(t("cli.module.promote_skill.generated"))
        print(f"- {target.as_posix()}")
        print("")
        print(t("cli.module.promote_skill.references", module=module_name))
        print(f"- .harbor/views/modules/{module_name}/module-card.md")
        print(f"- .harbor/views/modules/{module_name}/review-checklist.md")
        print(f"- .harbor/views/modules/{module_name}/debug-playbook.md")
    elif args.command == "project" and args.project_cmd == "structure":
        context = collect_project_structure_context(Path.cwd())
        markdown = generate_project_structure_markdown(context)
        workspace_paths = load_workspace_paths(Path.cwd(), enforce_write_safety=True)
        canonical_display = workspace_paths.project_structure_path.as_posix()
        try:
            canonical_display = workspace_paths.project_structure_path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except Exception:
            canonical_display = workspace_paths.project_structure_path.as_posix()
        if not args.write:
            print(markdown)
            print("")
            print(t("cli.project.structure.preview_only", path=canonical_display))
            if not context.has_indexed_modules:
                print(t("cli.project.structure.no_index"))
            return
        write_result = write_project_structure(context, Path.cwd())
        updated_paths = [write_result.canonical_path] + list(write_result.exported_paths)
        print(t("cli.project.structure.updated"))
        for updated in updated_paths:
            updated_display = updated.as_posix()
            try:
                updated_display = updated.resolve().relative_to(Path.cwd().resolve()).as_posix()
            except Exception:
                updated_display = updated.as_posix()
            print(f"- {updated_display}")
        if not context.has_indexed_modules:
            print(t("cli.project.structure.no_index"))
    elif args.command == "log" and getattr(args, "log_cmd", None) == "draft":
        try:
            payload = build_diary_draft(
                repo_root=Path.cwd(),
                since_last_accept=bool(getattr(args, "since_last_accept", False)),
                since_last_log=bool(getattr(args, "since_last_log", False)),
                from_report=Path(args.from_report) if getattr(args, "from_report", None) else None,
            )
            draft_ready = str(payload.get("draft_status") or "") == "ready"
            cache_result = (
                write_latest_diary_draft_cache(payload, repo_root=Path.cwd())
                if draft_ready
                else {
                    "markdown_path": None,
                    "json_path": None,
                    "markdown_path_display": ".harbor/state/log/latest-draft.md",
                    "json_path_display": ".harbor/state/log/latest-draft.json",
                    "warnings": [],
                }
            )
            rendered = serialize_diary_draft(payload, args.format)
            output_target = None
            explicit_output = bool(getattr(args, "output", None))
            save_requested = bool(getattr(args, "save", False))
            if explicit_output:
                output_target = write_diary_draft_output(
                    payload,
                    Path(args.output),
                    output_format=args.format,
                    repo_root=Path.cwd(),
                )
            elif save_requested:
                output_target = write_diary_draft_output(
                    payload,
                    build_saved_diary_draft_output_path(output_format=args.format, repo_root=Path.cwd()),
                    output_format=args.format,
                    repo_root=Path.cwd(),
                )
            if args.format == "json":
                _emit_json_stdout(payload)
            else:
                print(rendered, end="")
            if draft_ready and args.format != "json":
                print(_build_log_draft_next_actions_text())
            if draft_ready and cache_result.get("markdown_path") and args.format != "json":
                print(
                    t(
                        "cli.log.draft.cached",
                        markdown_path=cache_result["markdown_path_display"],
                        json_path=cache_result["json_path_display"],
                    ),
                    file=sys.stderr,
                )
            if args.format != "json":
                for warning in list(cache_result.get("warnings") or []):
                    print(t("cli.log.draft.cache_warning", message=str(warning)), file=sys.stderr)
            if explicit_output and save_requested and args.format != "json":
                print(
                    t(
                        "cli.log.draft.output_preferred",
                        path=_to_repo_relative_display(output_target) if output_target is not None else str(args.output),
                    ),
                    file=sys.stderr,
                )
            elif output_target is not None and args.format != "json":
                print(
                    t("cli.log.draft.saved", path=_to_repo_relative_display(output_target)),
                    file=sys.stderr,
                )
        except LogDraftError as exc:
            print(str(exc), file=sys.stderr)
            raise SystemExit(1)
    elif args.command == "log" and getattr(args, "log_cmd", None) == "write":
        try:
            preview = build_log_write_preview(
                repo_root=Path.cwd(),
                from_draft=Path(args.from_draft) if getattr(args, "from_draft", None) else None,
                from_latest_draft=bool(getattr(args, "from_latest_draft", False)),
            )
            if not getattr(args, "yes", False):
                if not _is_log_write_interactive():
                    print(t("cli.log.write.non_interactive_requires_yes"), file=sys.stderr)
                    raise SystemExit(1)
                print(
                    t(
                        "cli.log.write.preview",
                        summary=preview["summary"],
                        source_draft=preview["source_draft"],
                    )
                )
                choice = Prompt.ask(t("cli.log.write.confirm"), choices=["y", "n", "Y", "N"], default="N")
                if choice.upper() != "Y":
                    print(t("cli.log.write.canceled"))
                    return
            result = write_diary_entry_from_draft(
                repo_root=Path.cwd(),
                from_draft=Path(args.from_draft) if getattr(args, "from_draft", None) else None,
                from_latest_draft=bool(getattr(args, "from_latest_draft", False)),
                write_source="harbor log write --from-draft"
                if getattr(args, "from_draft", None)
                else "harbor log write --from-latest-draft"
                if bool(getattr(args, "from_latest_draft", False))
                else "harbor log write",
            )
            _print_log_write_from_draft_result(result)
        except LogDraftError as exc:
            print(_render_log_write_error(exc), file=sys.stderr)
            raise SystemExit(1)
    elif args.command == "log" and args.export:
        mgr = DiaryManager()
        md = mgr.export_markdown(since=args.since, min_visibility=args.visibility or "repo")
        print(md)
    elif args.command == "log" and args.message:
        mgr = DiaryManager()
        try:
            entry = mgr.log(
                summary=args.message,
                type=args.type,
                importance=args.importance,
                visibility=args.visibility,
                details=args.details,
                ref_commit=args.ref_commit,
                author=args.author,
                ts=args.ts,
            )
        except ValueError as exc:
            print(_render_log_message_error(exc), file=sys.stderr)
            raise SystemExit(1)
        _print_log_write_result(entry, mgr)
    elif args.command == "log":
        console = Console()
        with console.status("[bold blue][Status] Analyzing code changes...", spinner="dots"):
            eng = SyncEngine()
            rep = eng.check_status()
        if (rep.counts.get("drift", 0) + rep.counts.get("modified", 0)) == 0:
            print(t("cli.log.nochanges"))
            print(f"\n{t('cli.log.tip1')}")
            print(t("cli.log.tip2"))
            print(t("cli.log.tip3"))
            return
        drafter = DiaryDrafter(sync_engine=eng)
        try:
            with console.status("[bold magenta][AI] Drafting diary entry...", spinner="line"):
                draft = drafter.generate_draft()
        except LLMNotConfiguredError as e:
            print(str(e))
            print(t("cli.log.llm_env_hint"))
            return
        except Exception as e:
            msg = str(e)
            lc = msg.lower()
            if ("context" in lc and "length" in lc) or ("token" in lc and ("too many" in lc or "exceed" in lc)) or ("maximum context" in lc) or ("prompt too long" in lc):
                print(t("cli.log.context_too_long"))
                choice = Prompt.ask(t("cli.log.ask_simplify"), choices=["Y", "N", "y", "n"], default="Y")
                if choice.upper() == "Y":
                    with console.status("[bold magenta][AI] Drafting with simplified context...", spinner="line"):
                        try:
                            draft = drafter.generate_draft(limit=6000)
                        except Exception as e2:
                            print(t("cli.log.ai_failed", msg=str(e2)))
                            if args.debug:
                                provider = resolve_provider()
                                print(f"[DEBUG] Provider: {provider.name} Model: {getattr(provider, 'model', 'n/a')}")
                                if getattr(drafter, "last_prompt", None):
                                    print(f"[DEBUG] Prompt >>>\n{drafter.last_prompt or ''}")
                                if getattr(drafter, "last_output", None):
                                    print(f"[DEBUG] Raw <<<\n{drafter.last_output or ''}")
                            return
                else:
                    return
            else:
                print(t("cli.log.ai_failed", msg=str(e)))
                if args.debug:
                    provider = resolve_provider()
                    print(f"[DEBUG] Provider: {provider.name} Model: {getattr(provider, 'model', 'n/a')}")
                    print("[DEBUG] Ensure endpoint supports JSON structured output (response_format=json_object).")
                    print("[DEBUG] For ERNIE-compatible endpoints, set HARBOR_LLM_BASE_URL and HARBOR_LLM_MODEL=ernie-4.0.")
                    if getattr(drafter, "last_prompt", None):
                        print(f"[DEBUG] Prompt >>>\n{drafter.last_prompt or ''}")
                    if getattr(drafter, "last_output", None):
                        print(f"[DEBUG] Raw <<<\n{drafter.last_output or ''}")
                return
        if not draft:
            print(t("cli.log.nochanges"))
            return
        panel_text = (
            f"[bold]{t('cli.log.panel.summary')}[/bold]: {draft.get('summary','')}\n"
            f"[bold]{t('cli.log.panel.type')}[/bold]: {draft.get('type','')}\n"
            f"[bold]{t('cli.log.panel.importance')}[/bold]: {draft.get('importance','')}\n"
            f"[bold]{t('cli.log.panel.details')}[/bold]:\n{draft.get('details','')}"
        )
        console.print(Panel(panel_text, title=t("cli.log.panel.title"), border_style="green"))
        choice = Prompt.ask(t("cli.log.ask_save"), choices=["Y", "E", "N", "y", "e", "n"], default="Y")
        ans = choice.upper()
        if ans == "N":
            print(t("cli.log.discarded"))
            return
        summary_final = draft.get("summary", "")
        if ans == "E":
            summary_final = Prompt.ask(t("cli.log.ask_new_summary"), default=summary_final)
        mgr = DiaryManager()
        entry = mgr.log(
            summary=summary_final,
            type=draft.get("type", "chore"),
            importance=draft.get("importance", "normal"),
            visibility=args.visibility or "repo",
            details=draft.get("details"),
        )
        _print_log_write_result(entry, mgr)
    elif args.command == "adopt":
        console = Console()
        eng = DecoratorEngine()
        candidates = eng.scan(args.path, strategy=args.strategy)
        table = Table(title=t("cli.adopt.table.title"))
        table.add_column(t("cli.adopt.table.action"))
        table.add_column(t("cli.adopt.table.func"))
        table.add_column(t("cli.adopt.table.file"))
        table.add_column(t("cli.adopt.table.hasdoc"))
        table.add_column(t("cli.adopt.table.hasscope"))
        doc_yes = 0
        doc_no = 0
        for c in candidates:
            if c.has_docstring:
                doc_yes += 1
            else:
                doc_no += 1
            table.add_row(c.action, c.qualified_name, c.file_path.as_posix(), "Y" if c.has_docstring else "N", "Y" if c.has_scope_tag else "N")
        console.print(table)
        missing_scope_files = {}
        for c in candidates:
            if c.action == "Keep" and c.has_docstring and not c.has_scope_tag:
                missing_scope_files[c.file_path.as_posix()] = c.file_path
        create_docs_files = {}
        if args.strategy == "aggressive":
            for c in candidates:
                if c.action == "Create" and not c.has_docstring:
                    create_docs_files[c.file_path.as_posix()] = c.file_path
        target_files = {}
        for k, v in missing_scope_files.items():
            target_files[k] = v
        for k, v in create_docs_files.items():
            target_files[k] = v
        plans = []
        singleline_skipped_total = 0
        for f in target_files.values():
            for p in eng.preview(f, strategy=args.strategy):
                plans.append(p)
                if p.will_write and p.diff_preview:
                    pass
        summary = t("cli.adopt.summary", total=len(candidates), doc_yes=doc_yes, doc_no=doc_no)
        print(summary)
        to_apply = [p for p in plans if p.will_write]
        print(t("cli.adopt.planned", count=len(to_apply)))
        if args.dry_run:
            for p in to_apply:
                if p.diff_preview:
                    print(p.diff_preview)
            return
        if not args.yes:
            choice = Prompt.ask(t("cli.adopt.apply_prompt", count=len(to_apply)), choices=["y", "n", "Y", "N"], default="N")
            if choice.upper() != "Y":
                print(t("cli.adopt.nochanges"))
                return
        rep = eng.apply(to_apply, dry_run=False, strategy=args.strategy)
        data = _load_cfg_data_safe()
        roots = data.get("code_roots", [])
        p_in = Path(args.path)
        base = p_in.parent if p_in.is_file() else p_in
        try:
            rel = base.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except Exception:
            rel = base.as_posix()
        pattern = f"{rel}/**" if base.is_dir() else rel
        if pattern not in roots:
            roots.append(pattern)
        adopted_roots = data.get("adopted_roots", [])
        if pattern not in adopted_roots:
            adopted_roots.append(pattern)
        data["code_roots"] = roots
        data["adopted_roots"] = adopted_roots
        data.setdefault("exclude_paths", [])
        data.setdefault("profile", data.get("profile", "enforce_l3"))
        data.setdefault("language", data.get("language", "auto"))
        _write_cfg_data(data)
        print(t("cli.adopt.applied", files=len(rep.changed_files)))
        print(t("cli.adopt.added_config", path=pattern))
    elif args.command == "init":
        wiz = InitWizard(
            cwd=Path.cwd(),
            options=InitWizardOptions(
                force=getattr(args, "force", False),
                dry_run=getattr(args, "dry_run", False),
                language=getattr(args, "language", None),
                project=getattr(args, "project", None),
                governance=getattr(args, "governance", None),
                governance_docs=getattr(args, "governance_docs", None),
                llm=getattr(args, "llm", None),
                advice_mode=getattr(args, "advice", None),
                update_gitignore=getattr(args, "update_gitignore", None),
            ),
        )
        wiz.run()
    elif args.command == "unadopt":
        data = _load_cfg_data_safe()
        roots = data.get("code_roots", [])
        p_in = Path(args.path)
        base = p_in.parent if p_in.is_file() else p_in
        try:
            rel = base.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except Exception:
            rel = base.as_posix()
        pattern = f"{rel}/**" if base.is_dir() else rel
        if pattern in roots:
            roots = [x for x in roots if x != pattern]
            data["code_roots"] = roots
            adopted = data.get("adopted_roots", [])
            if pattern in adopted:
                adopted = [x for x in adopted if x != pattern]
                data["adopted_roots"] = adopted
            _write_cfg_data(data)
            print(t("cli.config.removed", path=pattern))
        else:
            print(t("cli.config.nochanges"))

    if deprecated:
        Console().print(f"[yellow]{t('cli.deprecated', old=deprecated, new=argv_mapped[0])}[/yellow]")


if __name__ == "__main__":
    main()
