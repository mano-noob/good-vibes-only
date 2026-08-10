class ReviewComparisonService:

    @staticmethod
    def compare(previous, current):

        if previous is None:

            return {
                "new_buy": [],
                "removed_buy": [],
                "new_watchlist": [],
                "removed_watchlist": []
            }

        def symbols(items):

            return {

                item["symbol"]

                for item in items

            }

        previous_buy = symbols(
            previous["buy"]
        )

        current_buy = symbols(
            current["buy"]
        )

        previous_watch = symbols(

            previous.get(
                "full_watchlist",
                previous["watchlist"]
            )

        )

        current_watch = symbols(

            current.get(
                "full_watchlist",
                current["watchlist"]
            )

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
                )

        }