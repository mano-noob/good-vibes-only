from app.core.config_service import ConfigService


class RiskManagementService:

    @staticmethod
    def _settings_value(settings, key, default):

        if isinstance(settings, dict):
            value = settings.get(key, default)
            if value is not None:
                return value

        return ConfigService.get(key, default)

    @staticmethod
    def calculate_position_size(entry_price, atr, available_cash, settings=None):

        if entry_price is None or atr is None or available_cash is None:
            return 0

        entry_price = float(entry_price)
        atr = float(atr)
        available_cash = float(available_cash)

        settings = settings or {}

        risk_per_trade_pct = float(
            RiskManagementService._settings_value(settings, "risk_per_trade_pct", 2)
        )
        atr_multiplier = float(
            RiskManagementService._settings_value(settings, "atr_multiplier", 2)
        )

        risk_amount = available_cash * (risk_per_trade_pct / 100.0)
        stop_distance = atr * atr_multiplier

        if entry_price <= 0 or atr <= 0 or stop_distance <= 0:
            return 0

        return max(0, risk_amount / stop_distance)

    @staticmethod
    def calculate_stop(entry_price, atr, settings=None):

        if entry_price is None or atr is None:
            return 0

        entry_price = float(entry_price)
        atr = float(atr)
        settings = settings or {}
        atr_multiplier = float(
            RiskManagementService._settings_value(settings, "atr_multiplier", 2)
        )

        return max(0.0, entry_price - (atr * atr_multiplier))

    @staticmethod
    def calculate_target(entry_price, atr, settings=None):

        if entry_price is None or atr is None:
            return 0

        entry_price = float(entry_price)
        atr = float(atr)
        settings = settings or {}
        atr_multiplier = float(
            RiskManagementService._settings_value(settings, "atr_multiplier", 2)
        )
        target_rr = float(
            RiskManagementService._settings_value(settings, "target_rr", 2.5)
        )

        stop_distance = atr * atr_multiplier
        return max(0.0, entry_price + (stop_distance * target_rr))

    @staticmethod
    def calculate_risk_reward(entry_price, atr, settings=None):

        if entry_price is None or atr is None:
            return 0

        settings = settings or {}
        target_rr = float(
            RiskManagementService._settings_value(settings, "target_rr", 2.5)
        )

        return float(target_rr)

    @staticmethod
    def calculate_trade(entry_price, atr, available_cash, settings=None):

        settings = settings or {}
        entry_price = float(entry_price)
        atr = float(atr)
        available_cash = float(available_cash)

        risk_per_trade_pct = float(
            RiskManagementService._settings_value(settings, "risk_per_trade_pct", 2)
        )
        atr_multiplier = float(
            RiskManagementService._settings_value(settings, "atr_multiplier", 2)
        )

        risk_amount = available_cash * (risk_per_trade_pct / 100.0)
        stop_distance = atr * atr_multiplier
        initial_stop = RiskManagementService.calculate_stop(entry_price, atr, settings)
        target_price = RiskManagementService.calculate_target(entry_price, atr, settings)
        risk_reward = RiskManagementService.calculate_risk_reward(entry_price, atr, settings)

        position_size = RiskManagementService.calculate_position_size(
            entry_price=entry_price,
            atr=atr,
            available_cash=available_cash,
            settings=settings,
        )

        if stop_distance > 0:
            position_size = max(0, int(position_size))
        else:
            position_size = 0

        capital_required = position_size * entry_price if position_size else 0
        allocation_pct = (
            (capital_required / available_cash) * 100.0 if available_cash else 0.0
        )

        return {
            "position_size": int(position_size),
            "capital_required": round(capital_required, 2),
            "risk_amount": round(risk_amount, 2),
            "initial_stop": round(initial_stop, 2),
            "target_price": round(target_price, 2),
            "risk_reward": round(risk_reward, 2),
            "allocation_pct": round(allocation_pct, 2),
        }
