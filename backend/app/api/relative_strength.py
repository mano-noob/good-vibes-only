from fastapi import APIRouter

from app.services.relative_strength_service import (
    RelativeStrengthService
)

router = APIRouter()


@router.get("/")
def rankings():

    return (
        RelativeStrengthService
        .get_rankings()
    )


@router.get("/top")
def top_stocks():

    return (
        RelativeStrengthService
        .get_top_stocks(30)
    )