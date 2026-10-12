from app.core.config_service import ConfigService
from app.core.watchlist import NIFTY_100
from app.services.market_data import MarketDataService


class RelativeStrengthService:

    LOOKBACK_3M = ConfigService.get("relative_strength_3m_lookback", 63)
    LOOKBACK_6M = ConfigService.get("relative_strength_6m_lookback", 126)
    LOOKBACK_12M = ConfigService.get("relative_strength_12m_lookback", 252)

    WEIGHT_3M = ConfigService.get("relative_strength_3m_weight", 0.30)
    WEIGHT_6M = ConfigService.get("relative_strength_6m_weight", 0.30)
    WEIGHT_12M = ConfigService.get("relative_strength_12m_weight", 0.40)

    @staticmethod
    def get_rankings(
        return_data=False
    ):

        rankings = []

        for symbol in NIFTY_100:

            try:
                # print(f"Downloading {symbol}")
                df = (
                    MarketDataService
                    .get_stock_data(
                        symbol=symbol,
                        period="2y"
                    )
                )

                if len(df) < 252:
                    continue

                current = float(
                    df["Close"].iloc[-1]
                )

                three_month = float(
                    df["Close"].iloc[-RelativeStrengthService.LOOKBACK_3M]
                )

                six_month = float(
                    df["Close"].iloc[-RelativeStrengthService.LOOKBACK_6M]
                )

                twelve_month = float(
                    df["Close"].iloc[-RelativeStrengthService.LOOKBACK_12M]
                )

                score = (

                    (
                        (
                            current
                            - twelve_month
                        )
                        / twelve_month
                    ) * 100 * RelativeStrengthService.WEIGHT_12M

                    +

                    (
                        (
                            current
                            - six_month
                        )
                        / six_month
                    ) * 100 * RelativeStrengthService.WEIGHT_6M

                    +

                    (
                        (
                            current
                            - three_month
                        )
                        / three_month
                    ) * 100 * RelativeStrengthService.WEIGHT_3M

                )

                entry = {

                    "symbol": symbol,

                    "score": round(score, 2)

                }

                if return_data:

                    entry["df"] = df

                rankings.append(entry)

            except Exception as e:

                print(
                    f"RS Error {symbol}: {e}"
                )

        return sorted(

            rankings,

            key=lambda x: x["score"],

            reverse=True
        )

    @staticmethod
    def get_top_stocks(
        top_percent: int = 20
    ):

        rankings = (
            RelativeStrengthService
            .get_rankings(
                return_data=False
            )
        )

        if not rankings:
            return []

        count = max(
            1,
            int(
                len(rankings)
                * top_percent
                / 100
            )
        )

        return [

            stock["symbol"]

            for stock in rankings[:count]

        ]