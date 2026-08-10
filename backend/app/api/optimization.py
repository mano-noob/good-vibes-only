from fastapi import APIRouter

from app.services.optimization_service import (
    OptimizationService
)

router = APIRouter()


@router.get("/")
def optimize():

    return OptimizationService.optimize()