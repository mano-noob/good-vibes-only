import math

from app.services.market_data import MarketDataService
from app.indicators.technical_indicators import TechnicalIndicators
from app.strategies.breakout_strategy import BreakoutStrategy
from app.services.ai_analysis_service import AIAnalysisService


class TradingService:

    @staticmethod
    def safe_float(value):

        if value is None:
            return None

        if isinstance(value, float):

            if math.isnan(value) or math.isinf(value):
                return None

        return float(round(value, 2))
    
    @staticmethod
    def explain_signal(signal):

            if signal["signal"] == "BUY":

                return "All strategy conditions satisfied."

            d = signal["diagnostics"]

            reasons = []

            if not d["breakout"]:
                reasons.append("Waiting for breakout")

            if not d["volume_confirmation"]:
                reasons.append("Volume below confirmation level")

            if not d["rsi_confirmation"]:
                reasons.append("RSI below threshold")

            if not d["trend_confirmation"]:
                reasons.append("Long-term trend not bullish")

            if not d["consolidation"]:
                reasons.append("No proper consolidation")

            return ", ".join(reasons)

    @staticmethod
    def calculate_readiness(signal):

        if signal["signal"] == "BUY":

            return 100

        score = 0

        d = signal["diagnostics"]

        if d["trend_confirmation"]:
            score += 25

        if d["breakout"]:
            score += 30

        if d["volume_confirmation"]:
            score += 20

        if d["rsi_confirmation"]:
            score += 15

        if d["consolidation"]:
            score += 10

        return score
    
        
    
    @staticmethod
    def analyze_stock(
        symbol: str,
        df=None
    ):

        if df is None:

            df = (
                MarketDataService
                .get_stock_data(symbol)
            )

        df["EMA20"] = TechnicalIndicators.calculate_ema(df)
        df["ATR"] = (
            TechnicalIndicators
            .calculate_atr(df)
        )

        df["RSI"] = TechnicalIndicators.calculate_rsi(df)

        df["EMA50"] = (
            TechnicalIndicators
            .calculate_ema50(df)
        )

        df["EMA200"] = (
            TechnicalIndicators
            .calculate_ema200(df)
        )

        signal = BreakoutStrategy.generate_signal(df)

        latest = df.iloc[-1]

        result = {

            "symbol": symbol,

            "close_price": TradingService.safe_float(
                latest["Close"]
            ),

            "ema20": TradingService.safe_float(
                latest["EMA20"]
            ),

            "ema50": TradingService.safe_float(
                latest["EMA50"]
            ),

            "ema200": TradingService.safe_float(
                latest["EMA200"]
            ),

            "atr": TradingService.safe_float(
                latest["ATR"]
            ),

            "rsi": TradingService.safe_float(
                latest["RSI"]
            ),

            "signal": signal
        }
        result["explanation"] = (

            TradingService

            .explain_signal(signal)

        )
        result["readiness_score"] = (

            TradingService

            .calculate_readiness(signal)

        )

        if (
            signal["signal"] == "BUY"
            and signal.get("reason")
        ):

            ai_analysis = (
                AIAnalysisService
                .generate_trade_analysis(result)
            )

            result["ai_analysis"] = ai_analysis

        else:

            result["ai_analysis"] = None

        return result