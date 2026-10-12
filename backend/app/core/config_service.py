import json
from pathlib import Path


class ConfigService:

    SETTINGS_PATH = Path(__file__).resolve().parents[2] / "config" / "settings.json"
    _CACHE = None

    @staticmethod
    def _load_file():

        if not ConfigService.SETTINGS_PATH.exists():
            return {}

        with ConfigService.SETTINGS_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return data if isinstance(data, dict) else {}

    @staticmethod
    def reload():

        ConfigService._CACHE = ConfigService._load_file()
        return ConfigService._CACHE

    @staticmethod
    def all():

        if ConfigService._CACHE is None:
            ConfigService.reload()

        return ConfigService._CACHE

    @staticmethod
    def get(key, default=None):

        config = ConfigService.all()

        if key is None:
            return config

        if "." not in key:
            return config.get(key, default)

        current = config
        for part in key.split("."):
            if not isinstance(current, dict):
                return default
            current = current.get(part, default)
            if current is default:
                return default

        return current
