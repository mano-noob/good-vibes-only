from fastapi import APIRouter

from app.core.api_response import error_response, success_response
from app.core.logger import LoggerService
from app.services.portfolio_backtest_service import PortfolioBacktestService

LoggerService.info_event("portfolio_backtest_loaded")

router = APIRouter()


@router.get("/")
def run_portfolio_backtest():
    try:
        return success_response(PortfolioBacktestService.run_portfolio_backtest())
    except Exception as exc:  # pragma: no cover - API error handling
        return error_response("Portfolio backtest failed", str(exc), 500)