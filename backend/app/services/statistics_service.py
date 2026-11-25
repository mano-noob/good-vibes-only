from __future__ import annotations

import json
from typing import Any, Dict, List

from runtime_paths import DATA_DIR, TRADES_FILE


class StatisticsService:

    DATA_DIR = DATA_DIR
    TRADES_FILE = TRADES_FILE

    @staticmethod
    def load() -> List[Dict[str, Any]]:
        StatisticsService.DATA_DIR.mkdir(parents=True, exist_ok=True)

        if not StatisticsService.TRADES_FILE.exists():
            with StatisticsService.TRADES_FILE.open("w", encoding="utf-8") as file:
                json.dump([], file, indent=4)
            return []

        with StatisticsService.TRADES_FILE.open("r", encoding="utf-8") as file:
            trades = json.load(file)

        if trades is None:
            return []

        if not isinstance(trades, list):
            return []

        return [trade for trade in trades if isinstance(trade, dict)]

    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        closed_trades = [
            trade for trade in StatisticsService.load()
            if str(trade.get("status", "")).upper() == "CLOSED"
        ]

        total_trades = len(closed_trades)
        wins = 0
        losses = 0
        gross_wins = 0.0
        gross_losses = 0.0
        total_holding_days = 0
        average_return = 0.0

        largest_win = 0.0
        largest_loss = 0.0

        for trade in closed_trades:
            profit_pct = float(trade.get("profit_pct", 0) or 0)
            holding_days = int(float(trade.get("holding_days", 0) or 0))
            total_holding_days += holding_days

            if profit_pct > 0:
                wins += 1
                gross_wins += profit_pct
                largest_win = max(largest_win, profit_pct)
            elif profit_pct < 0:
                losses += 1
                gross_losses += abs(profit_pct)
                largest_loss = min(largest_loss, profit_pct)

        if total_trades:
            average_return = sum(float(trade.get("profit_pct", 0) or 0) for trade in closed_trades) / total_trades

        win_rate = (wins / total_trades * 100) if total_trades else 0.0
        average_holding_days = (total_holding_days / total_trades) if total_trades else 0.0
        average_win = (gross_wins / wins) if wins else 0.0
        average_loss = (gross_losses / losses) if losses else 0.0
        expectancy = ((average_win * wins) - (average_loss * losses)) / total_trades if total_trades else 0.0
        profit_factor = (gross_wins / gross_losses) if gross_losses else (gross_wins if gross_wins > 0 else 0.0)

        return {
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "average_return": average_return,
            "average_holding_days": average_holding_days,
            "largest_win": largest_win,
            "largest_loss": largest_loss,
            "expectancy": expectancy,
            "profit_factor": profit_factor,
            "average_win": average_win,
            "average_loss": average_loss,
        }
