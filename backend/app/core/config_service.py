from typing import Any

from app.core.settings_service import SettingsService


class ConfigService:
    """Compatibility wrapper around the centralized runtime settings loader."""

    _CACHE: dict[str, Any] | None = None

    @staticmethod
    def reload() -> dict[str, Any]:
        ConfigService._CACHE = SettingsService.load()
        return ConfigService._CACHE

    @staticmethod
    def all() -> dict[str, Any]:
        if ConfigService._CACHE is None:
            ConfigService.reload()
        return ConfigService._CACHE or {}

    @staticmethod
    def get(key: str | None, default: Any = None) -> Any:
        config = ConfigService.all()

        if key is None:
            return config
        if "." not in key:
            return config.get(key, default)

        current: Any = config
        for part in key.split("."):
            if not isinstance(current, dict):
                return default
            current = current.get(part, default)
            if current is default:
                return default

        return current
