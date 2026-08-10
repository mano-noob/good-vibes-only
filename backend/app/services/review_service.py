from app.services.market_regime_service import (
    MarketRegimeService
)

from app.services.relative_strength_service import (
    RelativeStrengthService
)

from app.services.trading_service import (
    TradingService
)

from app.services.portfolio_service import (
    PortfolioService
)

from app.engines.decision_engine import (
    DecisionEngine
)

from datetime import datetime

from app.core.review_history import (
    ReviewHistory
)

from app.services.review_comparison_service import (
    ReviewComparisonService
)


class ReviewService:

    @staticmethod
    def generate_review():

        regime = (
            MarketRegimeService
            .get_market_regime()
        )

        top_stocks = sorted(

            RelativeStrengthService.get_rankings(
                return_data=True
            ),

            key=lambda x: x["score"],

            reverse=True

        )[:20]

        portfolio = (
            PortfolioService.load()
        )

        buy = []

        hold = []

        exit_list = []

        watchlist = []

        for stock in top_stocks:

            symbol = stock["symbol"]

            df = stock["df"]

            analysis = (
                TradingService
                .analyze_stock(
                    symbol=symbol,
                    df=df
                )
            )

            owned = (
                PortfolioService
                .is_owned(symbol)
            )

            decision = (
                DecisionEngine.decide(
                    symbol=symbol,
                    signal=analysis["signal"]["signal"],
                    owned=owned,
                    market_regime=regime
                )
            )

            analysis["decision"] = decision

            if decision["action"] == "BUY":

                buy.append(analysis)

            elif decision["action"] == "HOLD":

                hold.append(analysis)

            elif decision["action"] == "EXIT":

                exit_list.append(analysis)

            else:

                analysis["relative_strength"] = stock["score"]

                watchlist.append(analysis)

                watchlist = sorted(

                    watchlist,

                    key=lambda x: (

                        x["readiness_score"],

                        x["relative_strength"]

                    ),

                    reverse=True

                )

                full_watchlist = watchlist.copy()
        
        review = {

            "market_regime": regime,

            "buy": buy,

            "hold": hold,

            "exit": exit_list,

            "watchlist": watchlist[:10],
            "full_watchlist": full_watchlist,

            "portfolio_summary": {

                "cash": portfolio["cash"],

                "positions": len(
                    portfolio["positions"]
                )

            }

        }

        review["review_date"] = (
            datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            )
        )

        history = ReviewHistory.load()

        previous = (

            history[-1]

            if history

            else None

        )

        comparison = (

            ReviewComparisonService.compare(

                previous,

                review

            )

        )

        review["changes"] = comparison

        ReviewHistory.append(review)
        review.pop("full_watchlist", None)

        return review