from fastapi import APIRouter

from app.core.api_response import error_response, success_response
from app.core.stock_lifecycle import StockLifecycle
from app.services.review_service import ReviewService

router = APIRouter()


@router.get("/")
def review():
    try:
        return success_response(ReviewService.generate_review())
    except Exception as exc:  # pragma: no cover - API error handling
        return error_response("Failed to generate review", str(exc), 500)


@router.get("/lifecycle")
def lifecycle():
    try:
        return success_response(StockLifecycle.load())
    except Exception as exc:  # pragma: no cover - API error handling
        return error_response("Failed to load lifecycle data", str(exc), 500)


@router.get("/lifecycle/{symbol}")
def lifecycle_symbol(symbol: str):
    try:
        data = StockLifecycle.load()
        return success_response(data.get(symbol))
    except Exception as exc:  # pragma: no cover - API error handling
        return error_response("Failed to load lifecycle symbol", str(exc), 500)
