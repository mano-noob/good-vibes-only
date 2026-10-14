from fastapi import APIRouter

from app.core.api_response import error_response, success_response
from app.engines.decision_engine import DecisionEngine

router = APIRouter()


@router.get("/")
def test():
    try:
        return success_response(
            DecisionEngine.decide(
                symbol="SBIN.NS",
                signal="BUY",
                owned=False,
            )
        )
    except Exception as exc:  # pragma: no cover - API error handling
        return error_response("Decision evaluation failed", str(exc), 500)