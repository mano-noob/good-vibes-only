import copy
import json
from pathlib import Path
from typing import Any

from runtime_paths import DEFAULT_PORTFOLIO, DEFAULT_SETTINGS, PORTFOLIO_FILE, REVIEW_HISTORY_FILE, SETTINGS_FILE


class ValidationService:
    """Safely normalize runtime JSON payloads without crashing the application on malformed input."""

    @staticmethod
    def _safe_load_json(path: Path | None, default: Any) -> Any:
        if path is None or not path.exists():
            return copy.deepcopy(default)

        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (json.JSONDecodeError, TypeError, ValueError):
            return copy.deepcopy(default)

        return copy.deepcopy(default) if payload is None else payload

    @staticmethod
    def _safe_float(value: Any, fallback: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(fallback)

    @staticmethod
    def validate_portfolio(portfolio: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = portfolio if isinstance(portfolio, dict) else ValidationService._safe_load_json(PORTFOLIO_FILE, DEFAULT_PORTFOLIO)

        if not isinstance(payload, dict):
            payload = dict(DEFAULT_PORTFOLIO)

        positions = payload.get("positions", [])
        if not isinstance(positions, list):
            positions = []

        payload["positions"] = [position for position in positions if isinstance(position, dict)]
        payload.setdefault("cash", DEFAULT_PORTFOLIO["cash"])
        payload["cash"] = ValidationService._safe_float(payload.get("cash"), DEFAULT_PORTFOLIO["cash"])
        return payload

    @staticmethod
    def validate_trades(trades: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        normalized = trades if isinstance(trades, list) else ValidationService._safe_load_json(PORTFOLIO_FILE.parent / "trades.json", [])
        if not isinstance(normalized, list):
            return []
        return [trade for trade in normalized if isinstance(trade, dict)]

    @staticmethod
    def validate_review_history(history: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        normalized = history if isinstance(history, list) else ValidationService._safe_load_json(REVIEW_HISTORY_FILE, [])
        if not isinstance(normalized, list):
            return []
        return [entry for entry in normalized if isinstance(entry, dict)]

    @staticmethod
    def validate_settings(settings: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = settings if isinstance(settings, dict) else ValidationService._safe_load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
        if not isinstance(payload, dict):
            payload = {}

        for key, value in DEFAULT_SETTINGS.items():
            payload.setdefault(key, value)
        return payload

    @staticmethod
    def validate_runtime_data() -> dict[str, Any]:
        return {
            "portfolio": ValidationService.validate_portfolio(),
            "trades": ValidationService.validate_trades(),
            "review_history": ValidationService.validate_review_history(),
            "settings": ValidationService.validate_settings(),
        }
