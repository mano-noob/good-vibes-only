from fastapi import APIRouter

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