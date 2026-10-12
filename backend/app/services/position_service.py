from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional


class PositionService:

    @staticmethod
    def normalize_position(position: Optional[Dict[str, Any]]) -> Dict[str, Any]:

        if not isinstance(position, dict):
            position = {}

        normalized = dict(position)

        normalized.setdefault("symbol", "")
        normalized.setdefault("quantity", 0)
        normalized.setdefault("entry_price", 0.0)
        normalized.setdefault("entry_date", datetime.now().strftime("%Y-%m-%d"))
        normalized.setdefault("initial_stop", 0.0)
        normalized.setdefault("current_stop", normalized.get("initial_stop", 0.0))
        normalized.setdefault("highest_price", normalized.get("entry_price", 0.0))
        normalized.setdefault("highest_profit_pct", 0.0)
        normalized.setdefault("max_drawdown_pct", 0.0)
        normalized.setdefault("entry_priority", "")
        normalized.setdefault("entry_readiness", 0)
        normalized.setdefault("relative_strength", 0.0)
        normalized.setdefault("market_regime", "")
        normalized.setdefault("entry_signal", "")
        normalized.setdefault("strategy", "breakout")
        normalized.setdefault("status", "OPEN")
        normalized.setdefault("notes", "")

        return normalized

    @staticmethod
    def calculate_days_held(position: Optional[Dict[str, Any]]) -> int:

        position = PositionService.normalize_position(position)
        entry_date = position.get("entry_date")

        if not entry_date:
            return 0

        try:
            start = datetime.strptime(entry_date, "%Y-%m-%d").date()
        except ValueError:
            try:
                start = datetime.strptime(entry_date, "%Y-%m-%d %H:%M").date()
            except ValueError:
                return 0

        return max((datetime.now().date() - start).days, 0)

    @staticmethod
    def calculate_unrealized_pnl(position: Optional[Dict[str, Any]], current_price: Optional[float] = None) -> float:

        position = PositionService.normalize_position(position)
        quantity = float(position.get("quantity", 0) or 0)
        entry_price = float(position.get("entry_price", 0) or 0)
        current = float(current_price if current_price is not None else position.get("entry_price", 0) or 0)

        return (current - entry_price) * quantity

    @staticmethod
    def calculate_drawdown(position: Optional[Dict[str, Any]], current_price: Optional[float] = None) -> float:

        position = PositionService.normalize_position(position)
        entry_price = float(position.get("entry_price", 0) or 0)
        highest_price = float(position.get("highest_price", current_price if current_price is not None else entry_price) or 0)
        current = float(current_price if current_price is not None else position.get("entry_price", 0) or 0)

        if highest_price <= 0:
            return 0.0

        if current >= highest_price:
            return 0.0

        return ((highest_price - current) / highest_price) * 100

    @staticmethod
    def calculate_trailing_stop(
        position: Optional[Dict[str, Any]],
        current_price: Optional[float] = None,
        atr: Optional[float] = None
    ) -> float:

        position = PositionService.normalize_position(position)

        current_price_value = (
            float(current_price)
            if current_price is not None
            else float(position.get("entry_price", 0) or 0)
        )

        initial_stop = float(position.get("initial_stop", 0) or 0)
        current_stop = position.get("current_stop")
        highest_price = position.get("highest_price")

        if highest_price is None or float(highest_price) < current_price_value:
            highest_price = current_price_value

        current_stop_value = (
            float(current_stop)
            if current_stop is not None
            else initial_stop
        )

        if current_stop_value <= 0:
            current_stop_value = initial_stop

        if current_stop_value <= 0:
            current_stop_value = current_price_value

        if atr is not None:
            atr_value = float(atr)
            if atr_value > 0:
                current_stop_value = max(
                    current_stop_value,
                    float(highest_price) - (2 * atr_value),
                    initial_stop
                )
        else:
            current_stop_value = max(
                current_stop_value,
                initial_stop
            )

        return float(current_stop_value)

    @staticmethod
    def calculate_position_metrics(
        position: Optional[Dict[str, Any]],
        analysis: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:

        position = PositionService.normalize_position(position)
        analysis = analysis or {}

        quantity = float(position.get("quantity", 0) or 0)
        entry_price = float(position.get("entry_price", 0) or 0)
        current_price = float(analysis.get("close_price", position.get("entry_price", 0) or 0))

        market_value = quantity * current_price
        cost_basis = quantity * entry_price
        profit_amount = market_value - cost_basis
        profit_pct = (profit_amount / cost_basis * 100) if cost_basis else 0.0

        highest_price = float(position.get("highest_price", current_price) or current_price)
        if current_price > highest_price:
            highest_price = current_price

        drawdown_from_peak = 0.0
        if highest_price > 0 and current_price < highest_price:
            drawdown_from_peak = ((highest_price - current_price) / highest_price) * 100

        current_stop = position.get("current_stop")
        if current_stop is None:
            current_stop = position.get("initial_stop")
        if current_stop is None:
            current_stop = entry_price * 0.9

        current_stop = PositionService.calculate_trailing_stop(
            position=position,
            current_price=current_price,
            atr=analysis.get("atr")
        )

        return {
            "current_price": current_price,
            "market_value": market_value,
            "cost_basis": cost_basis,
            "profit_amount": profit_amount,
            "profit_pct": profit_pct,
            "highest_price": highest_price,
            "drawdown_from_peak": drawdown_from_peak,
            "days_held": PositionService.calculate_days_held(position),
            "current_stop": current_stop,
        }

    @staticmethod
    def update_position(
        position: Optional[Dict[str, Any]],
        analysis: Optional[Dict[str, Any]] = None,
        current_price: Optional[float] = None,
    ) -> Dict[str, Any]:

        position = PositionService.normalize_position(position)
        analysis = analysis or {}

        if current_price is None:
            current_price = analysis.get("close_price")

        if current_price is not None:
            highest_price = float(position.get("highest_price", current_price) or current_price)
            if float(current_price) > highest_price:
                highest_price = float(current_price)
            position["highest_price"] = highest_price

            position["current_stop"] = PositionService.calculate_trailing_stop(
                position=position,
                current_price=float(current_price),
                atr=analysis.get("atr")
            )

        position.setdefault("strategy", "breakout")
        position.setdefault("status", "OPEN")
        position.setdefault("notes", "")
        return position

    @staticmethod
    def calculate_position_health(
        position: Optional[Dict[str, Any]],
        analysis: Optional[Dict[str, Any]],
        metrics: Optional[Dict[str, float]] = None
    ) -> str:

        position = PositionService.normalize_position(position)
        analysis = analysis or {}
        metrics = metrics or PositionService.calculate_position_metrics(position, analysis)

        current_price = float(metrics.get("current_price", 0) or 0)
        ema20 = analysis.get("ema20")
        ema50 = analysis.get("ema50")
        ema200 = analysis.get("ema200")
        rsi = analysis.get("rsi")
        relative_strength = analysis.get("relative_strength")
        decision = analysis.get("decision") or {}

        if decision.get("action") == "EXIT":
            return "Exit Candidate"

        if ema200 is not None and current_price < float(ema200):
            return "Exit Candidate"

        if metrics.get("current_stop") is not None and current_price < float(metrics.get("current_stop")):
            return "Exit Candidate"

        if ema50 is not None and current_price < float(ema50):
            return "Weakening"

        if relative_strength is not None and float(relative_strength) < 50:
            return "Weakening"

        if ema20 is not None and current_price < float(ema20):
            return "Under Watch"

        if rsi is not None and float(rsi) < 50:
            return "Under Watch"

        trend_bullish = analysis.get("signal", {}).get("diagnostics", {}).get("trend_confirmation", False)

        if (
            ema20 is not None
            and ema50 is not None
            and rsi is not None
            and current_price > float(ema20)
            and current_price > float(ema50)
            and float(rsi) > 50
            and trend_bullish
        ):
            return "Healthy"

        if rsi is not None and float(rsi) > 50:
            return "Healthy"

        return "Under Watch"

    @staticmethod
    def generate_position_comment(
        health: str,
        analysis: Optional[Dict[str, Any]] = None,
    ) -> str:

        analysis = analysis or {}

        if health == "Healthy":
            return "Trend intact."

        if health == "Under Watch":
            if analysis.get("ema20") is not None and analysis.get("current_price") is not None and float(analysis["current_price"]) < float(analysis["ema20"]):
                return "Momentum softening below EMA20."
            if analysis.get("rsi") is not None and float(analysis["rsi"]) < 50:
                return "Momentum weakening below support."
            return "Monitor trend and momentum."

        if health == "Weakening":
            if analysis.get("ema50") is not None and analysis.get("current_price") is not None and float(analysis["current_price"]) < float(analysis["ema50"]):
                return "Below EMA50 and trend is fading."
            if analysis.get("relative_strength") is not None and float(analysis["relative_strength"]) < 50:
                return "Relative strength is deteriorating."
            return "Momentum weakening."

        if health == "Exit Candidate":
            if analysis.get("current_stop") is not None and analysis.get("current_price") is not None and float(analysis["current_price"]) < float(analysis["current_stop"]):
                return "Near trailing stop."
            if analysis.get("ema200") is not None and analysis.get("current_price") is not None and float(analysis["current_price"]) < float(analysis["ema200"]):
                return "Below long-term trend."
            return "Review exit plan."

        return "Position under review."

    @staticmethod
    def get_health_change_reason(
        previous_health: Optional[str],
        current_health: Optional[str],
        analysis: Optional[Dict[str, Any]] = None,
    ) -> str:

        analysis = analysis or {}
        current_price = analysis.get("current_price")
        ema20 = analysis.get("ema20")
        ema50 = analysis.get("ema50")
        ema200 = analysis.get("ema200")
        current_stop = analysis.get("current_stop")
        rsi = analysis.get("rsi")
        relative_strength = analysis.get("relative_strength")

        if current_health == "Healthy":
            return "Trend intact."

        if current_health == "Under Watch":
            if ema20 is not None and current_price is not None and float(current_price) < float(ema20):
                return "Closed below EMA20"
            if rsi is not None and float(rsi) < 50:
                return "RSI fell below 50"
            return "Momentum under pressure"

        if current_health == "Weakening":
            if ema50 is not None and current_price is not None and float(current_price) < float(ema50):
                return "Closed below EMA50"
            if relative_strength is not None and float(relative_strength) < 50:
                return "Relative strength deteriorating"
            return "Trend and momentum are fading"

        if current_health == "Exit Candidate":
            if ema200 is not None and current_price is not None and float(current_price) < float(ema200):
                return "Closed below EMA200"
            if current_stop is not None and current_price is not None and float(current_price) < float(current_stop):
                return "Price broke trailing stop"
            return "Exit conditions are building"

        if previous_health and current_health:
            return f"State changed from {previous_health} to {current_health}"

        return "Position status updated"
