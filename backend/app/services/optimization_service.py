from app.core.watchlist import NIFTY_50
from app.services.backtest_service import BacktestService


class OptimizationService:

    @staticmethod
    def optimize():

        parameter_sets = [

            (1, 2),
            (2, 4),
            (3, 6),
            (4, 8)

        ]

        results = []

        for stop_atr, target_atr in parameter_sets:

            portfolio_gross_profit = 0

            portfolio_gross_loss = 0

            tested = 0

            total_return = 0

            total_trades = 0

            for symbol in NIFTY_50:

                try:

                    result = (
                        BacktestService
                        .run_backtest(
                            symbol,
                            stop_atr,
                            target_atr
                        )
                    )

                    if (
                        result["profit_factor"]
                        is None
                    ):
                        continue

                    portfolio_gross_profit += (
                        result["gross_profit"]
                    )

                    portfolio_gross_loss += (
                        result["gross_loss"]
                    )

                    total_return += (
                        result["average_return"]
                    )

                    total_trades += result["trades"]

                    tested += 1

                except Exception as e:

                    print(
                        symbol,
                        e
                    )

            portfolio_pf = (
                round(
                    portfolio_gross_profit
                    /
                    portfolio_gross_loss,
                    2
                )
                if portfolio_gross_loss > 0
                else None
            )
            
            results.append(

                {

                    "stop_atr":
                        stop_atr,

                    "target_atr":
                        target_atr,

                    "portfolio_profit_factor":
                        portfolio_pf,

                    "average_return":
                        round(
                            total_return
                            / tested,
                            2
                        )
                        if tested > 0
                        else 0,

                    "stocks_tested": tested,

                    "total_trades":
    total_trades

                }
            )

        return sorted(

            results,

            key=lambda x:
                x["portfolio_profit_factor"]
                if x["portfolio_profit_factor"]
                else 0,

            reverse=True
        )