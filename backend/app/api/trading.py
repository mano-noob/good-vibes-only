from fastapi import APIRouter
from app.services.trading_service import TradingService
from app.services.trade_statistics_service import TradeStatisticsService

router = APIRouter()


@router.get("/analyze/{symbol}")
def analyze_stock(symbol: str):

    result = TradingService.analyze_stock(symbol)

    return result


@router.get("/statistics")
def statistics():

    return TradeStatisticsService.get_statistics()