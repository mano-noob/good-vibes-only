from fastapi import APIRouter

from app.engines.decision_engine import (
    DecisionEngine
)

router = APIRouter()


@router.get("/")
def test():

    return DecisionEngine.decide(

        symbol="SBIN.NS",

        signal="BUY",

        owned=False

    )