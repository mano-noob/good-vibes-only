from pathlib import Path
import os

base = Path(r"C:\Users\manoj\Trading_Agent\good-vibes-only\backend")
os.chdir(base)

from app.services.review_service import ReviewService

review = ReviewService.generate_review()
print(review["portfolio_summary"])
print(review["hold"][:1])
