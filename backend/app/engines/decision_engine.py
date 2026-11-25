from app.core.logger import LoggerService


class DecisionEngine:

    @staticmethod
    def is_exit_action(decision):

        return bool(decision) and decision.get("action") == "EXIT"

    @staticmethod
    def decide(
        symbol: str,
        signal: str,
        owned: bool,
        market_regime: str,
        exit_reason: str | None = None,
    ):

        LoggerService.info(f"DecisionEngine {symbol} signal={signal} regime={market_regime} owned={owned}")

        if owned:

            if exit_reason:
                return {
                    "action": "EXIT",
                    "reason": exit_reason,
                }

            if signal == "BUY":

                return {
                    "action": "HOLD",
                    "reason": "Existing position still satisfies entry conditions"
                }

            return {
                "action": "HOLD",
                "reason": "No new entry signal, but no explicit exit condition is present"
            }

        if (
            signal == "BUY"
            and market_regime == "Bullish"
        ):

            return {
                "action": "BUY",
                "reason": "Breakout confirmed in bullish market"
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