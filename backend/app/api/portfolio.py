from fastapi import APIRouter

from app.services.portfolio_analytics_service import PortfolioAnalyticsService

router = APIRouter()


@router.get("/analytics")
def portfolio_analytics():

    return PortfolioAnalyticsService.get_summary()
