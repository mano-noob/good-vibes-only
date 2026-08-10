print("PORTFOLIO BACKTEST FILE LOADED")
from fastapi import APIRouter

from app.services.portfolio_backtest_service import (
    PortfolioBacktestService
)

router = APIRouter()

@router.get("/")
def run_portfolio_backtest():

    return PortfolioBacktestService.run_portfolio_backtest()