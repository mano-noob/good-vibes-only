import math

from app.core.logger import LoggerService
from app.services.market_data import MarketDataService
from app.indicators.technical_indicators import (
    TechnicalIndicators
)


class MarketRegimeService:

    @staticmethod
    def is_bullish_ema(ema50, ema200):
        try:
            ema50_value = float(ema50)
            ema200_value = float(ema200)
        except (TypeError, ValueError):
            return None

        if not math.isfinite(ema50_value) or not math.isfinite(ema200_value):
            return None

        return ema50_value > ema200_value

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
            regime = MarketRegimeService.is_bullish_ema(
                latest["EMA50"],
                latest["EMA200"],
            )
            if regime is None:
                LoggerService.warning_event("market_regime_unavailable", reason="invalid_ema")
            return regime

        except Exception as e:

            LoggerService.error_event("market_regime_error", error=str(e))
            return None
        
    @staticmethod
    def get_market_regime():

        is_bull_market = MarketRegimeService.is_bull_market()

        if is_bull_market is None:
            return "Unknown"

        if is_bull_market:

            return "Bullish"

        return "Bearish"