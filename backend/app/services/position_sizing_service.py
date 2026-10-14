"""Buy-only position sizing for a single trade."""

from __future__ import annotations


class PositionSizingService:
    """Compute the position size based on total risk budget and stop distance."""

    PERCENT_SCALE = 100.0
    DEFAULT_RISK_PERCENT = 1.0

    @staticmethod
    def calculate(
        cash: float,
        entry_price: float,
        stop_price: float,
        risk_percent: float = DEFAULT_RISK_PERCENT,
    ) -> dict[str, float | int]:
        cash_value = float(cash or 0)
        entry_value = float(entry_price or 0)
        stop_value = float(stop_price or 0)
        risk_pct = float(risk_percent or 0)

        risk_capital = cash_value * (risk_pct / PositionSizingService.PERCENT_SCALE)
        risk_per_share = abs(entry_value - stop_value)

        if risk_per_share <= 0:
            return {
                "risk_capital": round(risk_capital, 2),
                "risk_per_share": 0.0,
                "shares": 0,
                "capital_required": 0.0,
                "capital_available": cash_value,
                "position_size_pct": 0.0,
            }

        shares = int(risk_capital // risk_per_share)
        capital_required = shares * entry_value

        if capital_required > cash_value:
            shares = int(cash_value // entry_value) if entry_value > 0 else 0
            capital_required = shares * entry_value

        position_size_pct = (capital_required / cash_value * PositionSizingService.PERCENT_SCALE) if cash_value else 0.0

        return {
            "risk_capital": round(risk_capital, 2),
            "risk_per_share": round(risk_per_share, 2),
            "shares": int(shares),
            "capital_required": round(capital_required, 2),
            "capital_available": cash_value,
            "position_size_pct": round(position_size_pct, 2),
        }
