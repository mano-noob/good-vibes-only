from fastapi import APIRouter

from app.core.api_response import error_response, success_response
from app.services.market_data import MarketDataService

router = APIRouter()


@router.get("/stock/{symbol}")
def get_stock(symbol: str):
    try:
        data = MarketDataService.get_stock_data(symbol)
        return success_response(data.tail(10).to_dict(orient="records"))
    except Exception as exc:  # pragma: no cover - API error handling
        return error_response("Failed to load market data", str(exc), 500)