from fastapi import APIRouter

from app.core.api_response import exception_response, success_response
from app.core.review_history import ReviewHistory
from app.services.portfolio_analytics_service import PortfolioAnalyticsService
from app.services.portfolio_service import PortfolioService
from app.services.review_service import ReviewService
from app.services.scheduler_service import scheduler

router = APIRouter()


@router.get("/health")
def health():
    try:
        portfolio = PortfolioService.load()
        return success_response({
            "status": "healthy",
            "version": "1.0.0",
            "scheduler": {
                "running": scheduler.running,
                "job_count": len(scheduler.get_jobs()),
            },
            "market_data": "available",
            "portfolio": {
                "cash": portfolio.get("cash", 0),
                "positions": len(portfolio.get("positions", [])),
            },
            "review_history": len(ReviewHistory.load()),
        })
    except Exception as exc:  # pragma: no cover - API error handling
        return exception_response("Health check failed", exc)


@router.get("/metrics")
def metrics():
    try:
        portfolio = PortfolioService.load()
        analytics = PortfolioAnalyticsService.get_summary()
        review = ReviewService.generate_review()

        return success_response({
            "portfolio": {
                "cash": portfolio.get("cash", 0),
                "positions": len(portfolio.get("positions", [])),
                "portfolio_value": analytics.get("portfolio_value", 0),
                "invested": analytics.get("invested", 0),
                "cash_pct": analytics.get("cash_pct", 0),
                "unrealized_pnl": analytics.get("unrealized_pnl", 0),
            },
            "review": {
                "buy_count": len(review.get("buy", [])),
                "hold_count": len(review.get("hold", [])),
                "exit_count": len(review.get("exit", [])),
                "watchlist_count": len(review.get("watchlist", [])),
                "market_regime": review.get("market_regime"),
            },
            "history_count": len(ReviewHistory.load()),
        })
    except Exception as exc:  # pragma: no cover - API error handling
        return exception_response("Metrics load failed", exc)
