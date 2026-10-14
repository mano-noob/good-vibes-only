from fastapi import APIRouter

from app.core.api_response import error_response, success_response
from app.services.optimization_service import OptimizationService

router = APIRouter()


@router.get("/")
def optimize():
    try:
        return success_response(OptimizationService.optimize())
    except Exception as exc:  # pragma: no cover - API error handling
        return error_response("Optimization failed", str(exc), 500)