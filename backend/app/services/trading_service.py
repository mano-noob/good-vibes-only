import math

from app.core.config_service import ConfigService
from app.services.market_data import MarketDataService
from app.indicators.technical_indicators import TechnicalIndicators
from app.strategies.breakout_strategy import BreakoutStrategy
from app.services.ai_analysis_service import AIAnalysisService
from app.services.risk_rating_service import RiskRatingService
from app.core.logger import LoggerService


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
    def calculate_priority(readiness_score):

        priority_map = ConfigService.get("priority", {"A": 90, "B": 75, "C": 60, "D": 40})

        if readiness_score >= priority_map.get("A", 90):
            return "A"

        if readiness_score >= priority_map.get("B", 75):
            return "B"

        if readiness_score >= priority_map.get("C", 60):
            return "C"

        if readiness_score >= priority_map.get("D", 40):
            return "D"

        return "IGNORE"
    
    @staticmethod
    def analyze_stock(
        symbol: str,
        df=None
    ):

        LoggerService.info(f"Trading analysis start {symbol}")
        start_time = __import__("datetime").datetime.now()

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
            TradingService.calculate_readiness(signal)
        )

        result["priority"] = (
            TradingService.calculate_priority(
                result["readiness_score"]
            )
        )
        result["risk_rating"] = RiskRatingService.rate({
            "rsi": result.get("rsi"),
            "atr": result.get("atr"),
            "atr_pct": (result.get("atr", 0) / result.get("close_price", 1) * 100) if result.get("close_price") else 0,
            "trend_confirmation": signal.get("diagnostics", {}).get("trend_confirmation", False),
            "market_regime": "Bullish",
            "signal": signal,
        })

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

        LoggerService.timing(f"TradingService.analyze_stock {symbol}", start_time)
        return result