from fastapi import APIRouter

from app.core.api_response import error_response, success_response
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
        return error_response("Failed to analyze symbol", str(exc), 500)


@router.get("/review")
def review():
    try:
        return success_response(ReviewService.get_latest_review())
    except Exception as exc:  # pragma: no cover - API error handling
        return error_response("Failed to load review", str(exc), 500)


@router.get("/statistics")
def statistics():
    try:
        return success_response(TradeStatisticsService.get_statistics())
    except Exception as exc:  # pragma: no cover - API error handling
        return error_response("Failed to load statistics", str(exc), 500)