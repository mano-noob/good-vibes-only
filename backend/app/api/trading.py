from fastapi import APIRouter

from app.core.api_response import exception_response, success_response
from app.services.review_service import ReviewService
from app.services.trade_statistics_service import TradeStatisticsService
from app.services.trading_service import TradingService

router = APIRouter()


@router.get("/analyze/{symbol}")
def analyze_stock(symbol: str):
    try:
        result = TradingService.analyze_stock(symbol)
        return success_response(result)
    except Exception as exc:  # pragma: no cover - API error handling
        return exception_response("Failed to analyze symbol", exc)


@router.get("/review")
def review():
    try:
        return success_response(ReviewService.get_latest_review())
    except Exception as exc:  # pragma: no cover - API error handling
        return exception_response("Failed to load review", exc)


@router.get("/statistics")
def statistics():
    try:
        return success_response(TradeStatisticsService.get_statistics())
    except Exception as exc:  # pragma: no cover - API error handling
        return exception_response("Failed to load statistics", exc)