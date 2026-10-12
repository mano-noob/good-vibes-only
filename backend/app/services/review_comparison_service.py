class ReviewComparisonService:

    @staticmethod
    def _get_watchlist(review):

        if not review:
            return []

        if "full_watchlist" in review:
            return review["full_watchlist"]

        return review.get("watchlist", [])

    @staticmethod
    def build_change_summary(comparison):

        if not comparison:
            return []

        summary = []

        for symbol in sorted(
            comparison.get("new_buy", [])
        ):
            summary.append(
                f"NEW BUY: {symbol}"
            )

        for symbol in sorted(
            comparison.get("removed_buy", [])
        ):
            summary.append(
                f"REMOVED BUY: {symbol}"
            )

        for item in sorted(
            comparison.get("readiness_changes", []),
            key=lambda x: (
                abs(x.get("score_change", 0)),
                x.get("symbol", "")
            ),
            reverse=True
        ):

            score_change = item.get("score_change")

            if score_change is None or score_change == 0:
                continue

            previous_score = item.get("previous_score")
            current_score = item.get("current_score")
            symbol = item.get("symbol", "")

            if score_change > 0:
                summary.append(
                    (
                        f"READINESS UP: {symbol} "
                        f"{previous_score} -> {current_score}"
                    )
                )
            else:
                summary.append(
                    (
                        f"READINESS DOWN: {symbol} "
                        f"{previous_score} -> {current_score}"
                    )
                )

        for symbol in sorted(
            comparison.get("new_watchlist", [])
        ):
            summary.append(
                f"NEW WATCHLIST: {symbol}"
            )

        for symbol in sorted(
            comparison.get("removed_watchlist", [])
        ):
            summary.append(
                f"REMOVED FROM WATCHLIST: {symbol}"
            )

        return summary

    @staticmethod
    def compare(previous, current):

        if previous is None:

            return {
                "new_buy": [],
                "removed_buy": [],
                "new_watchlist": [],
                "removed_watchlist": [],
                "readiness_changes": []
            }

        def symbols(items):

            return {
                item["symbol"]
                for item in items
            }

        def stock_map(items):

            return {
                item["symbol"]: item
                for item in items
            }

        previous_buy = symbols(
            previous.get("buy", [])
        )

        current_buy = symbols(
            current.get("buy", [])
        )

        previous_watch_items = ReviewComparisonService._get_watchlist(previous)
        current_watch_items = ReviewComparisonService._get_watchlist(current)

        previous_watch = symbols(
            previous_watch_items
        )

        current_watch = symbols(
            current_watch_items
        )

        if previous is not None:
            print(
                "Comparing current review against previous review"
            )
            print(
                f"Previous watchlist: {len(previous_watch)} | "
                f"Current watchlist: {len(current_watch)}"
            )

        previous_watch_map = stock_map(
            previous_watch_items
        )

        current_watch_map = stock_map(
            current_watch_items
        )

        readiness_changes = []

        common_symbols = (
            previous_watch
            & current_watch
        )

        diagnostic_names = {
            "breakout": "Breakout",
            "volume_confirmation": "Volume confirmation",
            "rsi_confirmation": "RSI confirmation",
            "trend_confirmation": "Trend confirmation",
            "consolidation": "Consolidation"
        }

        for symbol in common_symbols:

            previous_stock = previous_watch_map[symbol]
            current_stock = current_watch_map[symbol]

            previous_score = previous_stock.get(
                "readiness_score"
            )

            current_score = current_stock.get(
                "readiness_score"
            )

            previous_priority = previous_stock.get(
                "priority"
            )

            current_priority = current_stock.get(
                "priority"
            )

            previous_diagnostics = (
                previous_stock
                .get("signal", {})
                .get("diagnostics", {})
            )

            current_diagnostics = (
                current_stock
                .get("signal", {})
                .get("diagnostics", {})
            )

            condition_changes = []

            for key, label in diagnostic_names.items():

                previous_value = previous_diagnostics.get(
                    key
                )

                current_value = current_diagnostics.get(
                    key
                )

                if (
                    previous_value is False
                    and current_value is True
                ):

                    condition_changes.append(
                        f"{label} confirmed"
                    )

                elif (
                    previous_value is True
                    and current_value is False
                ):

                    condition_changes.append(
                        f"{label} lost"
                    )

            if (
                previous_score is not None
                and current_score is not None
                and previous_score != current_score
            ):

                score_change = (
                    current_score
                    - previous_score
                )

                readiness_changes.append(
                    {
                        "symbol": symbol,

                        "previous_score":
                            previous_score,

                        "current_score":
                            current_score,

                        "score_change":
                            score_change,

                        "direction": (
                            "UP"
                            if score_change > 0
                            else "DOWN"
                        ),

                        "previous_priority":
                            previous_priority,

                        "current_priority":
                            current_priority,

                        "condition_changes":
                            condition_changes
                    }
                )

        readiness_changes = sorted(
            readiness_changes,
            key=lambda x: (
                abs(x["score_change"]),
                x["symbol"]
            ),
            reverse=True
        )

        return {

            "new_buy":
                sorted(
                    current_buy - previous_buy
                ),

            "removed_buy":
                sorted(
                    previous_buy - current_buy
                ),

            "new_watchlist":
                sorted(
                    current_watch - previous_watch
                ),

            "removed_watchlist":
                sorted(
                    previous_watch - current_watch
                ),

            "readiness_changes":
                readiness_changes
        }