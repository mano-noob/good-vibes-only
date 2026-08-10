class DecisionEngine:

    @staticmethod
    def decide(
        symbol: str,
        signal: str,
        owned: bool,
        market_regime: str
    ):

        if owned:

            if signal == "BUY":

                return {
                    "action": "HOLD",
                    "reason": "Existing position still valid"
                }

            return {
                "action": "EXIT",
                "reason": "Strategy conditions no longer satisfied"
            }

        if (
            signal == "BUY"
            and market_regime == "Bullish"
        ):

            return {
                "action": "BUY",
                "reason": "Breakout in bullish market"
            }

        if (
            signal == "BUY"
            and market_regime == "Bearish"
        ):

            return {
                "action": "WATCHLIST",
                "reason": "Valid breakout but market is bearish"
            }

        return {
            "action": "WATCHLIST",
            "reason": "No valid entry"
        }