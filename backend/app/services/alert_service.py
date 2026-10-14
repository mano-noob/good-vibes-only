class AlertService:

    @staticmethod
    def generate(review):
        if not isinstance(review, dict):
            return []

        alerts = []
        review_buy = review.get("buy") or []
        review_hold = review.get("hold") or []
        review_exit = review.get("exit") or []
        changes = review.get("changes") or {}
        readiness_changes = changes.get("readiness_changes") or []
        market_regime = review.get("market_regime")
        previous_regime = review.get("previous_market_regime")

        for item in review_buy:
            symbol = item.get("symbol")
            if symbol:
                alerts.append({
                    "type": "BUY",
                    "message": f"New BUY signal for {symbol}"
                })

        for item in review_hold:
            symbol = item.get("symbol")
            if symbol:
                alerts.append({
                    "type": "HOLD",
                    "message": f"New HOLD signal for {symbol}"
                })
                health = item.get("holding_health")
                if health == "Weakening":
                    alerts.append({
                        "type": "HOLD",
                        "message": f"Holding weakened for {symbol}"
                    })
                elif health == "Healthy":
                    alerts.append({
                        "type": "HOLD",
                        "message": f"Holding at risk for {symbol}"
                    })

        for item in review_exit:
            symbol = item.get("symbol")
            if symbol:
                alerts.append({
                    "type": "EXIT",
                    "message": f"New EXIT signal for {symbol}"
                })
                decision = item.get("decision") or {}
                if str(decision.get("action") or "").upper() == "EXIT":
                    alerts.append({
                        "type": "STOP",
                        "message": "Stop loss hit"
                    })

        if market_regime and previous_regime and market_regime != previous_regime:
            alerts.append({
                "type": "MARKET",
                "message": f"Market regime changed from {previous_regime} to {market_regime}"
            })

        for item in readiness_changes:
            symbol = item.get("symbol")
            score_change = float(item.get("score_change", 0) or 0)
            if not symbol:
                continue
            if score_change >= 30:
                alerts.append({
                    "type": "READINESS",
                    "message": f"Readiness +30 for {symbol}"
                })
            elif score_change <= -30:
                alerts.append({
                    "type": "READINESS",
                    "message": f"Readiness -30 for {symbol}"
                })

        return alerts
