from app.core.stock_lifecycle import StockLifecycle


class StockLifecycleService:

    @staticmethod
    def process_review(review):

        review_date = review["review_date"]

        all_stocks = []

        all_stocks.extend(
            review.get("buy", [])
        )

        all_stocks.extend(
            review.get("hold", [])
        )

        all_stocks.extend(
            review.get("exit", [])
        )

        all_stocks.extend(
            review.get("watchlist", [])
        )

        results = []

        for stock in all_stocks:

            decision = stock.get(
                "decision",
                {}
            )

            signal = stock.get(
                "signal",
                {}
            )

            lifecycle = (
                StockLifecycle.update_stock(
                    symbol=stock["symbol"],
                    review_date=review_date,
                    status=decision.get(
                        "action",
                        "UNKNOWN"
                    ),
                    readiness_score=stock.get(
                        "readiness_score",
                        0
                    ),
                    priority=stock.get(
                        "priority",
                        "IGNORE"
                    ),
                    signal=signal.get(
                        "signal",
                        "UNKNOWN"
                    ),
                    decision=decision
                )
            )

            results.append(lifecycle)

        return results
