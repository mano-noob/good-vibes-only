from fastapi import APIRouter

from app.core.api_response import exception_response, success_response
from app.services.optimization_service import OptimizationService

router = APIRouter()


@router.get("/")
def optimize():
    try:
        return success_response(OptimizationService.optimize())
    except Exception as exc:  # pragma: no cover - API error handling
        return exception_response("Optimization failed", exc)