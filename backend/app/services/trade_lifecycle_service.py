from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.logger import LoggerService
from runtime_paths import DATA_DIR, TRADES_FILE


class TradeLifecycleService:

    DATA_DIR = DATA_DIR
    DATA_FILE = TRADES_FILE

    @staticmethod
    def load() -> List[Dict[str, Any]]:
        TradeLifecycleService.DATA_DIR.mkdir(parents=True, exist_ok=True)

        if not TradeLifecycleService.DATA_FILE.exists():
            TradeLifecycleService.save([])
            return []

        with TradeLifecycleService.DATA_FILE.open("r", encoding="utf-8") as file:
            trades = json.load(file)

        if trades is None:
            return []

        if not isinstance(trades, list):
            return []

        return [TradeLifecycleService._normalize_trade(trade) for trade in trades if isinstance(trade, dict)]

    @staticmethod
    def save(trades: List[Dict[str, Any]]) -> None:
        TradeLifecycleService.DATA_DIR.mkdir(parents=True, exist_ok=True)

        with TradeLifecycleService.DATA_FILE.open("w", encoding="utf-8") as file:
            json.dump(trades, file, indent=4)

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    @staticmethod
    def _normalize_trade(trade: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(trade)

        normalized.setdefault("trade_id", 0)
        normalized.setdefault("symbol", "")
        normalized.setdefault("status", "OPEN")
        normalized.setdefault("entry_date", datetime.now().strftime("%Y-%m-%d"))
        normalized.setdefault("entry_price", 0.0)
        normalized.setdefault("quantity", 0)
        normalized.setdefault("highest_price", normalized.get("entry_price", 0.0))
        normalized.setdefault("lowest_price", normalized.get("entry_price", 0.0))
        normalized.setdefault("current_price", normalized.get("entry_price", 0.0))
        normalized.setdefault("current_return_pct", 0.0)
        normalized.setdefault("holding_days", 0)
        normalized.setdefault("holding_health", "Neutral")
        normalized.setdefault("current_stop", normalized.get("entry_price", 0.0))
        normalized.setdefault("exit_date", None)
        normalized.setdefault("exit_price", None)
        normalized.setdefault("exit_reason", "")
        normalized.setdefault("profit_pct", 0.0)
        normalized.setdefault("profit_amount", 0.0)

        return normalized

    @staticmethod
    def _find_trade(trades: List[Dict[str, Any]], symbol: str) -> Optional[Dict[str, Any]]:
        for trade in trades:
            if str(trade.get("symbol", "")) == str(symbol):
                return trade
        return None

    @staticmethod
    def _calculate_holding_days(entry_date: Any) -> int:
        if not entry_date:
            return 0

        try:
            start = datetime.strptime(str(entry_date), "%Y-%m-%d").date()
        except ValueError:
            try:
                start = datetime.strptime(str(entry_date), "%Y-%m-%d %H:%M").date()
            except ValueError:
                return 0

        return max((datetime.now().date() - start).days, 0)

    @staticmethod
    def _calculate_current_return(trade: Dict[str, Any]) -> float:
        entry_price = TradeLifecycleService._safe_float(trade.get("entry_price"), 0.0)
        current_price = TradeLifecycleService._safe_float(trade.get("current_price"), entry_price)

        if entry_price == 0:
            return 0.0

        return ((current_price - entry_price) / entry_price) * 100

    @staticmethod
    def _determine_health(current_return_pct: float) -> str:
        if current_return_pct >= 5:
            return "Healthy"
        if current_return_pct <= -5:
            return "Weakening"
        return "Neutral"

    @staticmethod
    def _next_trade_id(trades: List[Dict[str, Any]]) -> int:
        trade_ids = [
            int(float(trade.get("trade_id", 0) or 0))
            for trade in trades
            if isinstance(trade.get("trade_id"), (int, float)) or str(trade.get("trade_id", "")).isdigit()
        ]
        return max(trade_ids, default=0) + 1

    @staticmethod
    def create_trade(trade_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        data = dict(trade_data or {})
        symbol = str(data.get("symbol") or "").strip()
        if not symbol:
            raise ValueError("symbol is required")

        trades = TradeLifecycleService.load()
        entry_price = TradeLifecycleService._safe_float(data.get("entry_price"), 0.0)
        quantity = int(float(data.get("quantity") or 0))
        entry_date = data.get("entry_date") or datetime.now().strftime("%Y-%m-%d")

        trade = {
            "trade_id": TradeLifecycleService._next_trade_id(trades),
            "symbol": symbol,
            "status": "OPEN",
            "entry_date": entry_date,
            "entry_price": entry_price,
            "quantity": quantity,
            "highest_price": entry_price,
            "lowest_price": entry_price,
            "current_price": entry_price,
            "current_return_pct": 0.0,
            "holding_days": 0,
            "holding_health": "Neutral",
            "current_stop": data.get("current_stop", entry_price),
            "exit_date": None,
            "exit_price": None,
            "exit_reason": "",
            "profit_pct": 0.0,
            "profit_amount": 0.0,
        }

        trades.append(trade)
        TradeLifecycleService.save(trades)
        LoggerService.info_event(
            "trade_opened",
            trade_id=trade["trade_id"],
            symbol=symbol,
            entry_price=entry_price,
            quantity=quantity,
            entry_date=entry_date,
        )
        return trade

    @staticmethod
    def update_trade(symbol: str, updates: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        if not symbol:
            return None

        trades = TradeLifecycleService.load()
        trade = TradeLifecycleService._find_trade(trades, symbol)
        if trade is None:
            return None

        payload = dict(updates or {})

        if "current_price" in payload:
            trade["current_price"] = TradeLifecycleService._safe_float(payload.get("current_price"), trade.get("current_price", 0.0))

        if "highest_price" in payload:
            trade["highest_price"] = TradeLifecycleService._safe_float(payload.get("highest_price"), trade.get("highest_price", trade.get("entry_price", 0.0)))
        else:
            trade["highest_price"] = max(
                TradeLifecycleService._safe_float(trade.get("highest_price"), trade.get("entry_price", 0.0)),
                TradeLifecycleService._safe_float(trade.get("current_price"), trade.get("entry_price", 0.0)),
            )

        if "lowest_price" in payload:
            trade["lowest_price"] = TradeLifecycleService._safe_float(payload.get("lowest_price"), trade.get("lowest_price", trade.get("entry_price", 0.0)))
        else:
            trade["lowest_price"] = min(
                TradeLifecycleService._safe_float(trade.get("lowest_price"), trade.get("entry_price", 0.0)),
                TradeLifecycleService._safe_float(trade.get("current_price"), trade.get("entry_price", 0.0)),
            )

        if "holding_days" in payload:
            trade["holding_days"] = int(float(payload.get("holding_days") or 0))
        else:
            trade["holding_days"] = TradeLifecycleService._calculate_holding_days(trade.get("entry_date"))

        if "current_return_pct" in payload:
            trade["current_return_pct"] = TradeLifecycleService._safe_float(payload.get("current_return_pct"), 0.0)
        else:
            trade["current_return_pct"] = TradeLifecycleService._calculate_current_return(trade)

        if "holding_health" in payload:
            trade["holding_health"] = payload.get("holding_health") or TradeLifecycleService._determine_health(trade["current_return_pct"])
        else:
            trade["holding_health"] = TradeLifecycleService._determine_health(trade["current_return_pct"])

        if "current_stop" in payload:
            trade["current_stop"] = TradeLifecycleService._safe_float(payload.get("current_stop"), trade.get("current_stop", trade.get("entry_price", 0.0)))

        for key, value in payload.items():
            if key in {"current_price", "highest_price", "lowest_price", "holding_days", "current_return_pct", "holding_health", "current_stop"}:
                continue
            trade[key] = value

        TradeLifecycleService.save(trades)
        LoggerService.info_event(
            "trade_updated",
            trade_id=trade.get("trade_id"),
            symbol=symbol,
            current_price=trade.get("current_price"),
            highest_price=trade.get("highest_price"),
            lowest_price=trade.get("lowest_price"),
            holding_days=trade.get("holding_days"),
            current_return_pct=trade.get("current_return_pct"),
            holding_health=trade.get("holding_health"),
            current_stop=trade.get("current_stop"),
        )
        return trade

    @staticmethod
    def close_trade(symbol: str, exit_price: Optional[float] = None, exit_reason: Optional[str] = None, exit_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        trades = TradeLifecycleService.load()
        trade = TradeLifecycleService._find_trade(trades, symbol)
        if trade is None:
            return None

        entry_price = TradeLifecycleService._safe_float(trade.get("entry_price"), 0.0)
        quantity = int(float(trade.get("quantity") or 0))
        exit_price_value = TradeLifecycleService._safe_float(exit_price, trade.get("current_price", entry_price))
        exit_date_value = exit_date or datetime.now().strftime("%Y-%m-%d")

        trade["status"] = "CLOSED"
        trade["exit_date"] = exit_date_value
        trade["exit_price"] = exit_price_value
        trade["exit_reason"] = exit_reason or trade.get("exit_reason") or ""
        trade["current_price"] = exit_price_value
        trade["holding_days"] = TradeLifecycleService._calculate_holding_days(trade.get("entry_date"))
        trade["current_return_pct"] = TradeLifecycleService._calculate_current_return({**trade, "current_price": exit_price_value})
        trade["holding_health"] = "Closed"

        if quantity and entry_price:
            trade["profit_amount"] = (exit_price_value - entry_price) * quantity
            trade["profit_pct"] = ((exit_price_value - entry_price) / entry_price) * 100
        else:
            trade["profit_amount"] = 0.0
            trade["profit_pct"] = 0.0

        TradeLifecycleService.save(trades)
        LoggerService.info_event(
            "trade_closed",
            trade_id=trade.get("trade_id"),
            symbol=symbol,
            exit_price=exit_price_value,
            exit_reason=exit_reason,
            profit_pct=trade.get("profit_pct"),
            profit_amount=trade.get("profit_amount"),
            holding_days=trade.get("holding_days"),
        )
        return trade

    @staticmethod
    def get_open_trade(symbol: str) -> Optional[Dict[str, Any]]:
        return next((trade for trade in TradeLifecycleService.load() if str(trade.get("symbol", "")) == str(symbol) and str(trade.get("status", "")).upper() == "OPEN"), None)

    @staticmethod
    def get_open_trades() -> List[Dict[str, Any]]:
        return [trade for trade in TradeLifecycleService.load() if str(trade.get("status", "")).upper() == "OPEN"]

    @staticmethod
    def get_closed_trades() -> List[Dict[str, Any]]:
        return [trade for trade in TradeLifecycleService.load() if str(trade.get("status", "")).upper() == "CLOSED"]
