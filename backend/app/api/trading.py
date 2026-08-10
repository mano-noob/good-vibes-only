from fastapi import APIRouter
from app.services.trading_service import TradingService

router = APIRouter()


@router.get("/analyze/{symbol}")
def analyze_stock(symbol: str):

    result = TradingService.analyze_stock(symbol)

    return result