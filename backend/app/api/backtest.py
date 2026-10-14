from fastapi import APIRouter

from app.core.api_response import error_response, success_response
from app.services.backtest_service import BacktestService

router = APIRouter()


@router.get("/{symbol}")
def run_backtest(symbol: str):
    try:
        return success_response(BacktestService.run_backtest(symbol))
    except Exception as exc:  # pragma: no cover - API error handling
        return error_response("Backtest failed", str(exc), 500)