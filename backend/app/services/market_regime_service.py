from app.core.logger import LoggerService
from app.services.market_data import MarketDataService
from app.indicators.technical_indicators import (
    TechnicalIndicators
)


class MarketRegimeService:

    @staticmethod
    def is_bull_market():

        try:

            df = (
                MarketDataService
                .get_stock_data(
                    symbol="^NSEI",
                    period="1y"
                )
            )

            df["EMA50"] = (
                TechnicalIndicators
                .calculate_ema50(df)
            )

            df["EMA200"] = (
                TechnicalIndicators
                .calculate_ema200(df)
            )

            latest = df.iloc[-1]

            return bool(

                latest["EMA50"]

                >

                latest["EMA200"]

            )

        except Exception as e:

            LoggerService.error_event("market_regime_error", error=str(e))
            return True
        
    @staticmethod
    def get_market_regime():

        if MarketRegimeService.is_bull_market():

            return "Bullish"

        return "Bearish"