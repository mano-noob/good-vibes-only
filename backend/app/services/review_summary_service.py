from app.services.review_comparison_service import (
    ReviewComparisonService
)


class ReviewSummaryService:

    @staticmethod
    def generate(changes):

        return ReviewComparisonService.build_change_summary(changes)
