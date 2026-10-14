class ReviewSummaryService:

    PRIORITY_RANK = {
        "A": 4,
        "B": 3,
        "C": 2,
        "D": 1,
        "IGNORE": 0,
    }

    @staticmethod
    def _priority_rank(priority):

        return ReviewSummaryService.PRIORITY_RANK.get(
            str(priority or "IGNORE").upper(),
            0
        )

    @staticmethod
    def generate(review):

        if not isinstance(review, dict):
            return {
                "market": "",
                "portfolio": {
                    "net_worth": 0,
                    "cash": 0,
                    "invested": 0,
                    "positions": 0,
                    "unrealized_pnl": 0,
                },
                "holdings": {
                    "healthy": 0,
                    "weakening": 0,
                    "exit": 0,
                },
                "review": {
                    "new_buy": 0,
                    "new_watchlist": 0,
                    "removed_watchlist": 0,
                    "major_upgrades": 0,
                    "major_downgrades": 0,
                },
                "best_opportunity": {
                    "symbol": None,
                    "priority": None,
                    "readiness": 0,
                },
            }

        portfolio_summary = review.get("portfolio_summary") or {}
        cash = float(portfolio_summary.get("cash", 0) or 0)
        market_value = float(portfolio_summary.get("market_value", 0) or 0)
        positions = int(portfolio_summary.get("positions", 0) or 0)
        unrealized_pnl = float(portfolio_summary.get("unrealized_pnl", 0) or 0)

        hold = review.get("hold") or []
        exit_items = review.get("exit") or []
        watchlist = review.get("watchlist") or []
        changes = review.get("changes") or {}
        readiness_changes = changes.get("readiness_changes") or []

        healthy = sum(
            1
            for item in hold
            if item.get("holding_health") == "Healthy"
        )

        weakening = sum(
            1
            for item in hold
            if item.get("holding_health") == "Weakening"
        )

        exit_count = sum(
            1
            for item in exit_items
            if (item.get("decision") or {}).get("action") == "EXIT"
        )

        new_buy = len(changes.get("new_buy", []) or [])
        new_watchlist = len(changes.get("new_watchlist", []) or [])
        removed_watchlist = len(changes.get("removed_watchlist", []) or [])
        major_upgrades = sum(
            1
            for item in readiness_changes
            if float(item.get("score_change", 0) or 0) >= 30
        )
        major_downgrades = sum(
            1
            for item in readiness_changes
            if float(item.get("score_change", 0) or 0) <= -30
        )

        best_opportunity = {}
        if watchlist:
            best_item = sorted(
                watchlist,
                key=lambda item: (
                    ReviewSummaryService._priority_rank(item.get("priority")),
                    float(item.get("readiness_score", 0) or 0),
                    float(item.get("relative_strength", 0) or 0),
                ),
                reverse=True,
            )[0]

            best_opportunity = {
                "symbol": best_item.get("symbol"),
                "priority": best_item.get("priority"),
                "readiness": best_item.get("readiness_score"),
            }

        return {
            "market": review.get("market_regime", ""),
            "portfolio": {
                "net_worth": round(cash + market_value, 2),
                "cash": round(cash, 2),
                "invested": round(market_value, 2),
                "positions": positions,
                "unrealized_pnl": round(unrealized_pnl, 2),
            },
            "holdings": {
                "healthy": healthy,
                "weakening": weakening,
                "exit": exit_count,
            },
            "review": {
                "new_buy": new_buy,
                "new_watchlist": new_watchlist,
                "removed_watchlist": removed_watchlist,
                "major_upgrades": major_upgrades,
                "major_downgrades": major_downgrades,
            },
            "best_opportunity": best_opportunity,
        }
