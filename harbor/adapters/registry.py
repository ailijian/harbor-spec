from __future__ import annotations

from typing import Any, Dict, List, Optional

from harbor.adapters.python.parser import PythonAdapter


class AdapterRegistry:
    def __init__(
        self,
        enabled: Dict[str, bool],
        adapters: Dict[str, object],
    ) -> None:
        self._enabled = dict(enabled)
        self._adapters = dict(adapters)
        self._language_order = ["python", "typescript"]

    @classmethod
    def default(cls) -> "AdapterRegistry":
        return cls.from_config(None)

    @classmethod
    def from_config(cls, config: Optional[Dict[str, Any]] = None) -> "AdapterRegistry":
        languages_cfg = cls._read_languages_config(config)

        python_enabled_cfg = cls._read_enabled_flag(languages_cfg, "python", default=True)
        typescript_enabled_cfg = cls._read_enabled_flag(languages_cfg, "typescript", default=False)

        availability = {
            "python": True,
            "typescript": False,  # v1.4.0 Task 2A: not implemented yet.
        }

        enabled = {
            "python": python_enabled_cfg and availability["python"],
            "typescript": typescript_enabled_cfg and availability["typescript"],
        }

        adapters: Dict[str, object] = {}
        if enabled["python"]:
            adapters["python"] = PythonAdapter()
        return cls(enabled=enabled, adapters=adapters)

    @staticmethod
    def _read_languages_config(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not isinstance(config, dict):
            return {}
        languages = config.get("languages")
        if not isinstance(languages, dict):
            return {}
        return languages

    @staticmethod
    def _read_enabled_flag(languages: Dict[str, Any], language: str, default: bool) -> bool:
        item = languages.get(language)
        if not isinstance(item, dict):
            return default
        value = item.get("enabled", default)
        if isinstance(value, bool):
            return value
        return default

    def get_enabled_languages(self) -> List[str]:
        enabled_languages = [lang for lang in self._language_order if self.is_enabled(lang)]
        dynamic_languages = sorted(
            lang
            for lang, is_on in self._enabled.items()
            if is_on and lang not in self._language_order
        )
        return enabled_languages + dynamic_languages

    def get_adapters(self) -> List[object]:
        return [self._adapters[lang] for lang in self.get_enabled_languages() if lang in self._adapters]

    def get_adapter(self, language: str) -> Optional[object]:
        normalized = language.strip().lower()
        return self._adapters.get(normalized)

    def is_enabled(self, language: str) -> bool:
        normalized = language.strip().lower()
        return bool(self._enabled.get(normalized, False))
