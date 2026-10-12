import json
from datetime import datetime
from pathlib import Path

from app.core.logger import LoggerService


class TradeJournalService:

    DATA_DIR = Path(__file__).resolve().parents[2] / "data"
    TRADE_HISTORY_FILE = DATA_DIR / "trade_history.json"

    @staticmethod
    def load():

        TradeJournalService.DATA_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        if not TradeJournalService.TRADE_HISTORY_FILE.exists():
            TradeJournalService.save([])
            return []

        with TradeJournalService.TRADE_HISTORY_FILE.open(
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)

        if data is None:
            return []

        return data

    @staticmethod
    def save(history):

        TradeJournalService.DATA_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        with TradeJournalService.TRADE_HISTORY_FILE.open(
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(history, f, indent=4)

    @staticmethod
    def append_trade(trade):

        LoggerService.info(f"Trade Recorded {trade.get('symbol')} {trade.get('trade_id')}")
        history = TradeJournalService.load()
        history.append(trade)
        TradeJournalService.save(history)

    @staticmethod
    def get_all():

        return TradeJournalService.load()

    @staticmethod
    def generate_trade_id():

        history = TradeJournalService.load()

        if not history:
            return 1

        return max(
            int(item.get("trade_id", 0))
            for item in history
        ) + 1
