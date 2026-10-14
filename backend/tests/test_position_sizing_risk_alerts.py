from app.services.alert_service import AlertService
from app.services.position_sizing_service import PositionSizingService
from app.services.risk_rating_service import RiskRatingService


def test_position_sizing_calculation():
    sizing = PositionSizingService.calculate(10000, 100, 90, risk_percent=1.0)

    assert sizing["risk_capital"] == 100.0
    assert sizing["risk_per_share"] == 10.0
    assert sizing["shares"] == 10
    assert sizing["capital_required"] == 1000.0
    assert sizing["capital_available"] == 10000
    assert sizing["position_size_pct"] == 10.0


def test_position_sizing_zero_risk_per_share():
    sizing = PositionSizingService.calculate(10000, 100, 100)
    assert sizing["shares"] == 0
    assert sizing["capital_required"] == 0.0


def test_risk_rating_service_rules():
    assert RiskRatingService.rate({"rsi": 80, "atr": 7, "market_regime": "Bearish", "signal": {"signal": "BUY"}}) == "HIGH"
    assert RiskRatingService.rate({"rsi": 60, "atr": 1.5, "trend_confirmation": True, "market_regime": "Bullish"}) == "LOW"
    assert RiskRatingService.rate({"rsi": 72, "atr": 3, "market_regime": "Bullish"}) == "MEDIUM"


def test_alert_generation_uses_existing_review_payload():
    review = {
        "market_regime": "Bearish",
        "buy": [{"symbol": "TITAN"}],
        "hold": [{"symbol": "INFY", "holding_health": "Weakening"}],
        "exit": [{"symbol": "RELIANCE", "decision": {"action": "EXIT"}}],
        "changes": {
            "readiness_changes": [
                {"symbol": "TCS", "score_change": 35},
                {"symbol": "HDFCBANK", "score_change": -35},
            ]
        },
    }

    alerts = AlertService.generate(review)
    messages = [item["message"] for item in alerts]

    assert any("New BUY signal for TITAN" in message for message in messages)
    assert any("Holding weakened for INFY" in message for message in messages)
    assert any("Stop loss hit" in message for message in messages) or any("Market regime changed" in message for message in messages)
