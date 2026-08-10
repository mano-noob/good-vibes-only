from fastapi import APIRouter
from app.services.market_data import MarketDataService

router = APIRouter()


@router.get("/stock/{symbol}")
def get_stock(symbol: str):

    data = MarketDataService.get_stock_data(symbol)

    return data.tail(10).to_dict(orient="records")