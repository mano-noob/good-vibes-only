from app.services.backtest_service import (
    BacktestService
)


class PortfolioBacktestService:

    STOP_ATR = 4
    TARGET_ATR = 8
    TOP_PERFORMERS = 5

    @staticmethod
    def average(values):

        values = [

            value

            for value in values

            if value is not None

        ]

        if not values:

            return 0

        return round(

            sum(values)

            / len(values),

            2

        )

    @staticmethod
    def run_portfolio_backtest():

        results = []

        total_trades = 0
        total_wins = 0
        total_losses = 0

        profit_factors = []
        avg_returns = []
        average_wins = []
        average_losses = []
        reward_risk_ratios = []
        expectancies = []

        top_stocks = [

            "POLYCAB.NS",
            "CUMMINSIND.NS",
            "ADANIENT.NS",
            "MOTHERSON.NS",
            "BANDHANBNK.NS",
            "ADANIPORTS.NS",
            "AUROPHARMA.NS",
            "SAIL.NS",
            "HINDALCO.NS",
            "SHRIRAMFIN.NS",
            "BOSCHLTD.NS",
            "TORNTPHARM.NS",
            "ABB.NS",
            "NMDC.NS",
            "APOLLOHOSP.NS",
            "EICHERMOT.NS",
            "ZYDUSLIFE.NS",
            "CHOLAFIN.NS",
            "GRASIM.NS",
            "PFC.NS"

        ]

        print(
            f"Selected {len(top_stocks)} stocks"
        )

        for symbol in top_stocks:

            print(f"Testing {symbol}")

            try:

                result = (
                    BacktestService
                    .run_backtest(
                        symbol,
                        stop_atr=PortfolioBacktestService.STOP_ATR,
                        target_atr=PortfolioBacktestService.TARGET_ATR
                    )
                )

                print(
                    f"Completed {symbol}"
                )

                if result["trades"] == 0:

                    continue

                results.append(result)

                total_trades += result["trades"]
                total_wins += result["wins"]
                total_losses += result["losses"]

                avg_returns.append(
                    result["average_return"]
                )

                profit_factors.append(
                    result["profit_factor"]
                )

                average_wins.append(
                    result["average_win"]
                )

                average_losses.append(
                    result["average_loss"]
                )

                reward_risk_ratios.append(
                    result["reward_risk_ratio"]
                )

                expectancies.append(
                    result["expectancy"]
                )

            except Exception as e:

                print(
                    f"Error testing {symbol}: {e}"
                )

        ranked = sorted(

            results,

            key=lambda x:
                x["profit_factor"]
                if x["profit_factor"]
                else 0,

            reverse=True

        )

        portfolio_win_rate = (

            round(

                total_wins

                / total_trades

                * 100,

                2

            )

            if total_trades

            else 0

        )

        return {

            "stocks_tested":

                len(results),

            "total_trades":

                total_trades,

            "wins":

                total_wins,

            "losses":

                total_losses,

            "portfolio_win_rate":

                portfolio_win_rate,

            "portfolio_avg_return":

                PortfolioBacktestService.average(
                    avg_returns
                ),

            "average_profit_factor":

                PortfolioBacktestService.average(
                    profit_factors
                ),

            "top_performers":

                ranked[
                    :PortfolioBacktestService.TOP_PERFORMERS
                ],

            "portfolio_average_win":

                PortfolioBacktestService.average(
                    average_wins
                ),

            "portfolio_average_loss":

                PortfolioBacktestService.average(
                    average_losses
                ),

            "portfolio_reward_risk":

                PortfolioBacktestService.average(
                    reward_risk_ratios
                ),

            "portfolio_expectancy":

                PortfolioBacktestService.average(
                    expectancies
                )

        }