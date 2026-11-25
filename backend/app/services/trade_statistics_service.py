from __future__ import annotations

import json

from runtime_paths import DATA_DIR, TRADE_HISTORY_FILE


class TradeStatisticsService:

    DATA_DIR = DATA_DIR
    TRADE_HISTORY_FILE = TRADE_HISTORY_FILE

    @staticmethod
    def _safe_round(value, digits=2):
        try:
            return round(float(value), digits)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def load_trades():

        TradeStatisticsService.DATA_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        if not TradeStatisticsService.TRADE_HISTORY_FILE.exists():
            return []

        with TradeStatisticsService.TRADE_HISTORY_FILE.open(
            "r",
            encoding="utf-8"
        ) as f:
            trades = json.load(f)

        if trades is None:
            return []

        if not isinstance(trades, list):
            return []

        return trades

    @staticmethod
    def get_statistics():

        trades = TradeStatisticsService.load_trades()

        total_trades = len(trades)
        wins = 0
        losses = 0
        gross_wins = 0.0
        gross_losses = 0.0
        total_holding_days = 0

        largest_winner = {}
        largest_loser = {}

        for trade in trades:
            if not isinstance(trade, dict):
                continue

            gross_profit = float(trade.get("gross_profit", 0) or 0)
            days_held = int(trade.get("days_held", 0) or 0)

            if gross_profit > 0:
                wins += 1
                gross_wins += gross_profit

                if not largest_winner or gross_profit > float(largest_winner.get("gross_profit", 0) or 0):
                    largest_winner = trade

            elif gross_profit < 0:
                losses += 1
                gross_losses += abs(gross_profit)

                if not largest_loser or gross_profit < float(largest_loser.get("gross_profit", 0) or 0):
                    largest_loser = trade

            total_holding_days += days_held

        win_rate = (wins / total_trades * 100) if total_trades else 0.0
        average_gain = (gross_wins / wins) if wins else 0.0
        average_loss = (gross_losses / losses) if losses else 0.0
        profit_factor = (gross_wins / gross_losses) if gross_losses else (gross_wins if gross_wins > 0 else 0.0)
        expectancy = ((average_gain * wins) - (average_loss * losses)) / total_trades if total_trades else 0.0
        average_holding_days = (total_holding_days / total_trades) if total_trades else 0.0

        return {
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate": TradeStatisticsService._safe_round(win_rate),
            "average_gain": TradeStatisticsService._safe_round(average_gain),
            "average_loss": TradeStatisticsService._safe_round(average_loss),
            "profit_factor": TradeStatisticsService._safe_round(profit_factor),
            "expectancy": TradeStatisticsService._safe_round(expectancy),
            "average_holding_days": TradeStatisticsService._safe_round(average_holding_days),
            "largest_winner": largest_winner,
            "largest_loser": largest_loser,
        }
