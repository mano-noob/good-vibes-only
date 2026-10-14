class RiskRatingService:

    @staticmethod
    def rate(stock):
        if not isinstance(stock, dict):
            return "MEDIUM"

        rsi = float(stock.get("rsi", 0) or 0)
        atr = float(stock.get("atr", 0) or 0)
        atr_pct = float(stock.get("atr_pct", 0) or 0)
        trend_confirmed = bool(stock.get("trend_confirmation"))
        market_regime = str(stock.get("market_regime") or "").lower()
        signal = stock.get("signal") or {}
        signal_name = str(signal.get("signal") or "").upper()
        is_buy_signal = signal_name == "BUY"

        if rsi > 75 or atr_pct > 5 or (market_regime == "bearish" and is_buy_signal):
            return "HIGH"

        if trend_confirmed and atr_pct < 2 and 55 <= rsi <= 70:
            return "LOW"

        if trend_confirmed and atr_pct < 2 and rsi >= 55:
            return "LOW"

        if atr > 0 and atr_pct < 2 and rsi <= 70:
            return "LOW"

        return "MEDIUM"
