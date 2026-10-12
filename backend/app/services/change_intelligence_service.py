class ChangeIntelligenceService:

    @staticmethod
    def _normalize_condition(label):

        text = label.strip()

        if text.endswith(" confirmed"):
            return text[:-len(" confirmed")], "confirmed"

        if text.endswith(" lost"):
            return text[:-len(" lost")], "lost"

        return text, "changed"

    @staticmethod
    def _join_condition_summary(conditions):

        if not conditions:
            return ""

        normalized = [
            ChangeIntelligenceService._normalize_condition(
                condition
            )
            for condition in conditions
        ]

        names = [name for name, _ in normalized]
        status = normalized[0][1]

        if len(names) == 1:
            return f"{names[0]} was {status}."

        if len(names) == 2:
            return (
                f"{names[0]} and {names[1].lower()} "
                f"were {status}."
            )

        joined_middle = ", ".join(
            name.lower() for name in names[1:-1]
        )
        return (
            f"{names[0]}, {joined_middle} and {names[-1].lower()} "
            f"were {status}."
        )

    @staticmethod
    def _format_readiness_message(item):

        symbol = item["symbol"]
        previous = item["previous_score"]
        current = item["current_score"]
        direction = item.get("direction")

        if direction == "UP":
            sentence = f"{symbol} readiness improved from {previous} to {current}."
        elif direction == "DOWN":
            sentence = f"{symbol} readiness fell from {previous} to {current}."
        else:
            sentence = f"{symbol} readiness changed from {previous} to {current}."

        previous_priority = item.get("previous_priority")
        current_priority = item.get("current_priority")

        if previous_priority and current_priority and previous_priority != current_priority:
            sentence += f" Priority changed from {previous_priority} to {current_priority}."

        condition_changes = item.get("condition_changes", [])

        if condition_changes:
            sentence += " " + ChangeIntelligenceService._join_condition_summary(condition_changes)

        return sentence

    @staticmethod
    def generate_summary(comparison):

        if not comparison:
            return []

        events = []

        for symbol in comparison.get("new_buy", []):
            events.append(
                {
                    "type": "NEW_BUY",
                    "symbol": symbol,
                    "message": f"{symbol} entered the BUY list."
                }
            )

        for symbol in comparison.get("removed_buy", []):
            events.append(
                {
                    "type": "REMOVED_BUY",
                    "symbol": symbol,
                    "message": f"{symbol} was removed from the BUY list."
                }
            )

        readiness_changes = []
        for item in comparison.get("readiness_changes", []):
            if item.get("score_change") is None:
                continue

            if item.get("score_change") == 0:
                continue

            readiness_changes.append(
                {
                    "type": "READINESS_CHANGE",
                    "symbol": item["symbol"],
                    "direction": item.get("direction", "UP" if item.get("score_change", 0) > 0 else "DOWN"),
                    "previous_score": item.get("previous_score"),
                    "current_score": item.get("current_score"),
                    "score_change": item.get("score_change"),
                    "previous_priority": item.get("previous_priority"),
                    "current_priority": item.get("current_priority"),
                    "condition_changes": item.get("condition_changes", []),
                    "message": ChangeIntelligenceService._format_readiness_message(item)
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

        events.extend(readiness_changes)

        for symbol in comparison.get("new_watchlist", []):
            events.append(
                {
                    "type": "NEW_WATCHLIST",
                    "symbol": symbol,
                    "message": f"{symbol} entered the watchlist."
                }
            )

        for symbol in comparison.get("removed_watchlist", []):
            events.append(
                {
                    "type": "REMOVED_WATCHLIST",
                    "symbol": symbol,
                    "message": f"{symbol} dropped from the watchlist."
                }
            )

        return events
