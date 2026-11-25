from fastapi import APIRouter

from app.core.api_response import exception_response, success_response
from app.services.relative_strength_service import RelativeStrengthService

router = APIRouter()


@router.get("/")
def rankings():
    try:
        return success_response(RelativeStrengthService.get_rankings())
    except Exception as exc:  # pragma: no cover - API error handling
        return exception_response("Failed to load rankings", exc)


@router.get("/top")
def top_stocks():
    try:
        return success_response(RelativeStrengthService.get_top_stocks(30))
    except Exception as exc:  # pragma: no cover - API error handling
        return exception_response("Failed to load top stocks", exc)