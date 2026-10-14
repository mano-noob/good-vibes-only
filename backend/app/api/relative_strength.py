from fastapi import APIRouter

from app.core.api_response import error_response, success_response
from app.services.relative_strength_service import RelativeStrengthService

router = APIRouter()


@router.get("/")
def rankings():
    try:
        return success_response(RelativeStrengthService.get_rankings())
    except Exception as exc:  # pragma: no cover - API error handling
        return error_response("Failed to load rankings", str(exc), 500)


@router.get("/top")
def top_stocks():
    try:
        return success_response(RelativeStrengthService.get_top_stocks(30))
    except Exception as exc:  # pragma: no cover - API error handling
        return error_response("Failed to load top stocks", str(exc), 500)