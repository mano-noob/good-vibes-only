from fastapi import APIRouter
from app.services.backtest_service import BacktestService

router = APIRouter()


@router.get("/{symbol}")
def run_backtest(symbol: str):

    return BacktestService.run_backtest(symbol)