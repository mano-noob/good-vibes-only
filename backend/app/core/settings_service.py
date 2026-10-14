import json
from pathlib import Path
from typing import Any

from runtime_paths import DEFAULT_SETTINGS, SETTINGS_FILE


class SettingsService:
    """Runtime settings provider that safely initializes and validates JSON configuration."""

    DEFAULTS: dict[str, Any] = DEFAULT_SETTINGS

    @staticmethod
    def _default_settings() -> dict[str, Any]:
        return json.loads(json.dumps(SettingsService.DEFAULTS))

    @staticmethod
    def _file_path() -> Path:
        return SETTINGS_FILE

    @staticmethod
    def load() -> dict[str, Any]:
        path = SettingsService._file_path()
        path.parent.mkdir(parents=True, exist_ok=True)

        if not path.exists():
            SettingsService.save(SettingsService._default_settings())
            return SettingsService._default_settings()

        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (json.JSONDecodeError, TypeError, ValueError):
            return SettingsService._default_settings()

        if not isinstance(payload, dict):
            return SettingsService._default_settings()

        merged = SettingsService._default_settings()
        merged.update(payload)
        return merged

    @staticmethod
    def save(settings: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = settings if isinstance(settings, dict) else SettingsService._default_settings()
        path = SettingsService._file_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=4)
        return payload

    @staticmethod
    def all() -> dict[str, Any]:
        return SettingsService.load()

    @staticmethod
    def get(key: str | None, default: Any = None) -> Any:
        config = SettingsService.all()
        if key is None:
            return config
        if "." not in key:
            return config.get(key, default)

        current: Any = config
        for fragment in key.split("."):
            if not isinstance(current, dict):
                return default
            current = current.get(fragment, default)
            if current is default:
                return default
        return current

    @staticmethod
    def update(patch: dict[str, Any] | None = None) -> dict[str, Any]:
        config = SettingsService.load()
        if isinstance(patch, dict):
            config.update(patch)
        SettingsService.save(config)
        return config
