from fastapi import APIRouter

from app.core.api_response import exception_response, success_response
from app.services.alert_service import AlertService
from app.services.market_regime_service import MarketRegimeService
from app.services.portfolio_analytics_service import PortfolioAnalyticsService
from app.services.portfolio_service import PortfolioService
from app.services.review_service import ReviewService
from app.services.trade_journal_service import TradeJournalService
from app.services.trade_statistics_service import TradeStatisticsService

router = APIRouter()


@router.get("")
@router.get("/")
def portfolio_overview():
    try:
        return success_response(PortfolioService.load())
    except Exception as exc:  # pragma: no cover - API error handling
        return exception_response("Failed to load portfolio", exc)


@router.get("/analytics")
def portfolio_analytics():
    try:
        return success_response(PortfolioAnalyticsService.get_summary())
    except Exception as exc:  # pragma: no cover - API error handling
        return exception_response("Failed to load portfolio analytics", exc)


@router.get("/statistics")
def portfolio_statistics():
    try:
        return success_response(TradeStatisticsService.get_statistics())
    except Exception as exc:  # pragma: no cover - API error handling
        return exception_response("Failed to load portfolio statistics", exc)


@router.get("/journal")
def portfolio_journal():
    try:
        return success_response(TradeJournalService.get_all())
    except Exception as exc:  # pragma: no cover - API error handling
        return exception_response("Failed to load journal", exc)


@router.get("/alerts")
def portfolio_alerts():
    try:
        review = ReviewService.generate_review()
        return success_response(AlertService.generate(review))
    except Exception as exc:  # pragma: no cover - API error handling
        return exception_response("Failed to generate alerts", exc)


@router.get("/watchlist")
def portfolio_watchlist():
    try:
        review = ReviewService.generate_review()
        return success_response(review.get("watchlist", []))
    except Exception as exc:  # pragma: no cover - API error handling
        return exception_response("Failed to load watchlist", exc)


@router.get("/market")
def portfolio_market():
    try:
        return success_response({"market_regime": MarketRegimeService.get_market_regime()})
    except Exception as exc:  # pragma: no cover - API error handling
        return exception_response("Failed to load market regime", exc)


@router.get("/summary")
def portfolio_summary():
    try:
        review = ReviewService.generate_review()
        return success_response(review.get("summary", {}))
    except Exception as exc:  # pragma: no cover - API error handling
        return exception_response("Failed to load portfolio summary", exc)