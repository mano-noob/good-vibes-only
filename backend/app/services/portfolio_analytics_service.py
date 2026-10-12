from app.services.portfolio_service import PortfolioService
from app.services.trade_journal_service import TradeJournalService


class PortfolioAnalyticsService:

    @staticmethod
    def get_summary():

        portfolio = PortfolioService.load()
        positions = portfolio.get("positions", [])
        trades = TradeJournalService.get_all()

        cash = float(portfolio.get("cash", 0) or 0)
        invested = 0.0
        largest_position = {}

        for position in positions:
            current_value = float(position.get("market_value", 0) or 0)
            if current_value <= 0:
                quantity = float(position.get("quantity", 0) or 0)
                entry_price = float(position.get("entry_price", 0) or 0)
                current_value = quantity * entry_price

            invested += current_value

            if not largest_position or current_value > float(largest_position.get("market_value", 0) or 0):
                largest_position = {
                    "symbol": position.get("symbol"),
                    "market_value": round(current_value, 2),
                }

        portfolio_value = cash + invested
        cash_pct = (cash / portfolio_value * 100) if portfolio_value else 0.0
        equity_pct = (invested / portfolio_value * 100) if portfolio_value else 0.0

        realized_pnl = 0.0
        trade_returns = []
        for trade in trades:
            realized_pnl += float(trade.get("gross_profit", 0) or 0)
            trade_returns.append(float(trade.get("return_pct", 0) or 0))

        unrealized_pnl = 0.0
        for position in positions:
            unrealized_pnl += float(position.get("profit_amount", 0) or 0)

        largest_winner = {}
        largest_loser = {}
        for trade in trades:
            gross_profit = float(trade.get("gross_profit", 0) or 0)
            if gross_profit > 0:
                if not largest_winner or gross_profit > float(largest_winner.get("gross_profit", 0) or 0):
                    largest_winner = {
                        "symbol": trade.get("symbol"),
                        "gross_profit": round(gross_profit, 2),
                    }
            elif gross_profit < 0:
                if not largest_loser or gross_profit < float(largest_loser.get("gross_profit", 0) or 0):
                    largest_loser = {
                        "symbol": trade.get("symbol"),
                        "gross_profit": round(gross_profit, 2),
                    }

        average_return = (
            sum(trade_returns) / len(trade_returns)
            if trade_returns
            else 0.0
        )

        portfolio_risk = "LOW"
        if invested > cash and average_return < 0:
            portfolio_risk = "MEDIUM"
        if average_return < -10:
            portfolio_risk = "HIGH"

        return {
            "portfolio_value": round(portfolio_value, 2),
            "cash": round(cash, 2),
            "invested": round(invested, 2),
            "cash_pct": round(cash_pct, 2),
            "equity_pct": round(equity_pct, 2),
            "realized_pnl": round(realized_pnl, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "largest_position": largest_position,
            "largest_winner": largest_winner,
            "largest_loser": largest_loser,
            "average_return": round(average_return, 2),
            "portfolio_risk": portfolio_risk,
        }
