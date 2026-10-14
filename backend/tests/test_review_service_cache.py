from app.core.review_history import ReviewHistory
from app.services.review_service import ReviewService


def test_latest_review_returns_cached_when_present(tmp_path, monkeypatch):
    cache_path = tmp_path / "review_history.json"
    ReviewHistory.FILE = cache_path
    ReviewHistory.save([
        {"market_regime": "Bullish", "summary": {"market": "Bullish"}}
    ])

    calls = {"count": 0}

    def fake_generate():
        calls["count"] += 1
        return {"market_regime": "Generated"}

    monkeypatch.setattr(ReviewService, "generate_review", fake_generate)

    latest = ReviewService.get_latest_review()

    assert latest["market_regime"] == "Bullish"
    assert calls["count"] == 0
