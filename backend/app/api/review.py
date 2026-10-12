from fastapi import APIRouter

from app.core.stock_lifecycle import (
    StockLifecycle
)

from app.services.review_service import (
    ReviewService
)

router = APIRouter()

@router.get("/")

def review():

    return (
        ReviewService
        .generate_review()
    )


@router.get("/lifecycle")
def lifecycle():

    return (
        StockLifecycle.load()
    )


@router.get("/lifecycle/{symbol}")
def lifecycle_symbol(symbol: str):

    data = StockLifecycle.load()

    return data.get(symbol)
