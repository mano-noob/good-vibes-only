import json
from pathlib import Path
from typing import Any, Dict, List


class TradeJournalService:
    """Write and read the trade journal used for portfolio statistics and review snapshots."""

    DATA_DIR = Path(__file__).resolve().parents[2] / "data"
    TRADES_FILE = DATA_DIR / "trades.json"

    @staticmethod
    def load() -> List[Dict[str, Any]]:
        TradeJournalService.DATA_DIR.mkdir(parents=True, exist_ok=True)

        if not TradeJournalService.TRADES_FILE.exists():
            with TradeJournalService.TRADES_FILE.open("w", encoding="utf-8") as file:
                json.dump([], file, indent=4)
            return []

        try:
            with TradeJournalService.TRADES_FILE.open("r", encoding="utf-8") as file:
                trades = json.load(file)
        except (json.JSONDecodeError, TypeError, ValueError):
            return []

        if trades is None:
            return []

        if not isinstance(trades, list):
            return []

        return [trade for trade in trades if isinstance(trade, dict)]

    @staticmethod
    def save(trades: List[Dict[str, Any]]) -> None:
        TradeJournalService.DATA_DIR.mkdir(parents=True, exist_ok=True)
        with TradeJournalService.TRADES_FILE.open("w", encoding="utf-8") as file:
            json.dump(trades, file, indent=4)

    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        return TradeJournalService.load()

    @staticmethod
    def append_trade(trade: Dict[str, Any]) -> Dict[str, Any]:
        trades = TradeJournalService.load()
        trades.append(trade)
        TradeJournalService.save(trades)
        return trade

    @staticmethod
    def generate_trade_id() -> int:
        trades = TradeJournalService.load()
        trade_ids = [
            int(float(trade.get("trade_id", 0) or 0))
            for trade in trades
            if isinstance(trade, dict) and str(trade.get("trade_id", "")).strip() not in ("", "None")
        ]
        return max(trade_ids, default=0) + 1

    @staticmethod
    def get_open_trades() -> List[Dict[str, Any]]:
        return [trade for trade in TradeJournalService.load() if str(trade.get("status", "")).upper() == "OPEN"]

    @staticmethod
    def get_closed_trades() -> List[Dict[str, Any]]:
        return [trade for trade in TradeJournalService.load() if str(trade.get("status", "")).upper() == "CLOSED"]
