"""Risk and trade-sizing calculations for position entries."""

from __future__ import annotations

from typing import Any

from app.core.config_service import ConfigService


class RiskManagementService:
    """Calculate stop, target, position sizing, and trade risk using settings-backed defaults."""

    PERCENT_SCALE = 100.0
    DEFAULT_RISK_PERCENT = 2.0
    DEFAULT_ATR_MULTIPLIER = 2.0
    DEFAULT_TARGET_RR = 2.5

    @staticmethod
    def _settings_value(settings: dict[str, Any] | None, key: str, default: Any) -> Any:
        if isinstance(settings, dict):
            value = settings.get(key, default)
            if value is not None:
                return value
        return ConfigService.get(key, default)

    @staticmethod
    def calculate_position_size(
        entry_price: float,
        atr: float,
        available_cash: float,
        settings: dict[str, Any] | None = None,
    ) -> float:
        if entry_price is None or atr is None or available_cash is None:
            return 0.0

        entry_value = float(entry_price)
        atr_value = float(atr)
        cash_value = float(available_cash)
        settings_dict = settings or {}

        risk_per_trade_pct = float(
            RiskManagementService._settings_value(settings_dict, "risk_per_trade_pct", RiskManagementService.DEFAULT_RISK_PERCENT)
        )
        atr_multiplier = float(
            RiskManagementService._settings_value(settings_dict, "atr_multiplier", RiskManagementService.DEFAULT_ATR_MULTIPLIER)
        )

        risk_amount = cash_value * (risk_per_trade_pct / RiskManagementService.PERCENT_SCALE)
        stop_distance = atr_value * atr_multiplier

        if entry_value <= 0 or atr_value <= 0 or stop_distance <= 0:
            return 0.0

        return max(0.0, risk_amount / stop_distance)

    @staticmethod
    def calculate_stop(
        entry_price: float,
        atr: float,
        settings: dict[str, Any] | None = None,
    ) -> float:
        if entry_price is None or atr is None:
            return 0.0

        entry_value = float(entry_price)
        atr_value = float(atr)
        settings_dict = settings or {}
        atr_multiplier = float(
            RiskManagementService._settings_value(settings_dict, "atr_multiplier", RiskManagementService.DEFAULT_ATR_MULTIPLIER)
        )
        return max(0.0, entry_value - (atr_value * atr_multiplier))

    @staticmethod
    def calculate_target(
        entry_price: float,
        atr: float,
        settings: dict[str, Any] | None = None,
    ) -> float:
        if entry_price is None or atr is None:
            return 0.0

        entry_value = float(entry_price)
        atr_value = float(atr)
        settings_dict = settings or {}
        atr_multiplier = float(
            RiskManagementService._settings_value(settings_dict, "atr_multiplier", RiskManagementService.DEFAULT_ATR_MULTIPLIER)
        )
        target_rr = float(
            RiskManagementService._settings_value(settings_dict, "target_rr", RiskManagementService.DEFAULT_TARGET_RR)
        )

        stop_distance = atr_value * atr_multiplier
        return max(0.0, entry_value + (stop_distance * target_rr))

    @staticmethod
    def calculate_risk_reward(
        entry_price: float,
        atr: float,
        settings: dict[str, Any] | None = None,
    ) -> float:
        if entry_price is None or atr is None:
            return 0.0

        settings_dict = settings or {}
        target_rr = float(
            RiskManagementService._settings_value(settings_dict, "target_rr", RiskManagementService.DEFAULT_TARGET_RR)
        )
        return float(target_rr)

    @staticmethod
    def calculate_trade(
        entry_price: float,
        atr: float,
        available_cash: float,
        settings: dict[str, Any] | None = None,
    ) -> dict[str, float | int]:
        settings_dict = settings or {}
        entry_value = float(entry_price)
        atr_value = float(atr)
        cash_value = float(available_cash)

        risk_per_trade_pct = float(
            RiskManagementService._settings_value(settings_dict, "risk_per_trade_pct", RiskManagementService.DEFAULT_RISK_PERCENT)
        )
        atr_multiplier = float(
            RiskManagementService._settings_value(settings_dict, "atr_multiplier", RiskManagementService.DEFAULT_ATR_MULTIPLIER)
        )

        risk_amount = cash_value * (risk_per_trade_pct / RiskManagementService.PERCENT_SCALE)
        stop_distance = atr_value * atr_multiplier
        initial_stop = RiskManagementService.calculate_stop(entry_value, atr_value, settings_dict)
        target_price = RiskManagementService.calculate_target(entry_value, atr_value, settings_dict)
        risk_reward = RiskManagementService.calculate_risk_reward(entry_value, atr_value, settings_dict)

        position_size = RiskManagementService.calculate_position_size(
            entry_price=entry_value,
            atr=atr_value,
            available_cash=cash_value,
            settings=settings_dict,
        )

        normalized_position_size = max(0, int(position_size)) if stop_distance > 0 else 0
        capital_required = normalized_position_size * entry_value if normalized_position_size else 0.0
        allocation_pct = ((capital_required / cash_value) * RiskManagementService.PERCENT_SCALE) if cash_value else 0.0

        return {
            "position_size": int(normalized_position_size),
            "capital_required": round(capital_required, 2),
            "risk_amount": round(risk_amount, 2),
            "initial_stop": round(initial_stop, 2),
            "target_price": round(target_price, 2),
            "risk_reward": round(risk_reward, 2),
            "allocation_pct": round(allocation_pct, 2),
        }
