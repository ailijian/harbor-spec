from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from harbor.core.workspace import load_workspace_config

AdviceMode = str


@dataclass(frozen=True)
class AdviceSettings:
    mode: AdviceMode = "basic"
    include_in_ci_json: bool = True
    include_in_text: bool = True

    @property
    def enabled(self) -> bool:
        return self.mode == "basic"


def _to_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("1", "true", "yes", "on"):
            return True
        if normalized in ("0", "false", "no", "off"):
            return False
    return default


def _normalize_mode(value: Any) -> AdviceMode:
    normalized = str(value or "").strip().lower()
    if normalized in ("off", "basic"):
        return normalized
    return "basic"


def _normalize_mode_optional(value: Any) -> Optional[AdviceMode]:
    normalized = str(value or "").strip().lower()
    if normalized in ("off", "basic"):
        return normalized
    return None


def _load_config_advice(repo_root: Path) -> dict:
    loaded = load_workspace_config(repo_root)
    config = loaded.get("config")
    if not isinstance(config, dict):
        return {}
    advice = config.get("advice")
    if isinstance(advice, dict):
        return dict(advice)
    return {}


def resolve_advice_settings(*, cli_advice: Optional[str], repo_root: Optional[Path] = None) -> AdviceSettings:
    root = (repo_root or Path.cwd()).resolve()
    config_advice = _load_config_advice(root)
    config_mode = _normalize_mode(config_advice.get("mode", "basic"))
    env_mode = _normalize_mode_optional(os.getenv("HARBOR_ADVICE_MODE", ""))
    cli_mode = _normalize_mode_optional(cli_advice or "")

    mode = config_mode
    if env_mode is not None:
        mode = env_mode
    if cli_mode is not None:
        mode = cli_mode

    include_in_ci_json = _to_bool(config_advice.get("include_in_ci_json", True), True)
    include_in_text = _to_bool(config_advice.get("include_in_text", True), True)
    return AdviceSettings(
        mode=mode,
        include_in_ci_json=include_in_ci_json,
        include_in_text=include_in_text,
    )
