from app.services.change_intelligence_service import ChangeIntelligenceService
from app.services.review_comparison_service import ReviewComparisonService


def test_first_review_has_no_summary():
    assert ChangeIntelligenceService.generate_summary({}) == []
    assert ChangeIntelligenceService.generate_summary(
        ReviewComparisonService.compare(None, {"buy": [], "full_watchlist": []})
    ) == []


def test_readiness_changes_have_expected_labels_and_messages():
    previous = {
        "buy": [],
        "full_watchlist": [
            {
                "symbol": "TITAN.NS",
                "readiness_score": 100,
                "priority": "A",
                "signal": {
                    "diagnostics": {
                        "breakout": True,
                        "volume_confirmation": True,
                        "rsi_confirmation": True,
                        "trend_confirmation": True,
                        "consolidation": True,
                    }
                },
            }
        ],
    }

    current = {
        "buy": [],
        "full_watchlist": [
            {
                "symbol": "TITAN.NS",
                "readiness_score": 50,
                "priority": "D",
                "signal": {
                    "diagnostics": {
                        "breakout": False,
                        "volume_confirmation": False,
                        "rsi_confirmation": True,
                        "trend_confirmation": True,
                        "consolidation": False,
                    }
                },
            }
        ],
    }

    comparison = ReviewComparisonService.compare(previous, current)

    readiness = comparison["readiness_changes"][0]
    assert readiness["previous_score"] == 100
    assert readiness["current_score"] == 50
    assert readiness["score_change"] == -50
    assert readiness["direction"] == "DOWN"
    assert readiness["previous_priority"] == "A"
    assert readiness["current_priority"] == "D"
    assert "Breakout lost" in readiness["condition_changes"]
    assert "Volume confirmation lost" in readiness["condition_changes"]
    assert "RSI confirmation confirmed" not in readiness["condition_changes"]

    summary = ChangeIntelligenceService.generate_summary(comparison)
    event = summary[2]
    assert event["type"] == "READINESS_CHANGE"
    assert event["symbol"] == "TITAN.NS"
    assert event["direction"] == "DOWN"
    assert event["score_change"] == -50
    assert "TITAN.NS readiness fell from 100 to 50." in event["message"]
    assert "Priority changed from A to D." in event["message"]
    assert "Breakout and volume confirmation were lost." in event["message"]


def test_score_increase_event_and_watchlist_buy_events():
    comparison = {
        "new_buy": ["ABC.NS"],
        "removed_buy": ["DEF.NS"],
        "new_watchlist": ["POLYCAB.NS"],
        "removed_watchlist": ["BAJFINANCE.NS"],
        "readiness_changes": [
            {
                "symbol": "DIVISLAB.NS",
                "previous_score": 40,
                "current_score": 70,
                "score_change": 30,
                "direction": "UP",
                "previous_priority": "D",
                "current_priority": "C",
                "condition_changes": ["Breakout confirmed"],
            }
        ],
    }

    summary = ChangeIntelligenceService.generate_summary(comparison)
    assert summary[0]["type"] == "NEW_BUY"
    assert summary[0]["message"] == "ABC.NS entered the BUY list."
    assert summary[1]["type"] == "REMOVED_BUY"
    assert summary[1]["message"] == "DEF.NS was removed from the BUY list."
    assert summary[2]["type"] == "READINESS_CHANGE"
    assert summary[2]["direction"] == "UP"
    assert summary[2]["score_change"] == 30
    assert "DIVISLAB.NS readiness improved from 40 to 70." in summary[2]["message"]
    assert "Priority changed from D to C." in summary[2]["message"]
    assert "Breakout was confirmed." in summary[2]["message"]
    assert summary[3]["type"] == "NEW_WATCHLIST"
    assert summary[3]["message"] == "POLYCAB.NS entered the watchlist."
    assert summary[4]["type"] == "REMOVED_WATCHLIST"
    assert summary[4]["message"] == "BAJFINANCE.NS dropped from the watchlist."


def test_multiple_conditions_are_joined_naturally():
    comparison = {
        "new_buy": [],
        "removed_buy": [],
        "new_watchlist": [],
        "removed_watchlist": [],
        "readiness_changes": [
            {
                "symbol": "XYZ.NS",
                "previous_score": 80,
                "current_score": 50,
                "score_change": -30,
                "direction": "DOWN",
                "previous_priority": "B",
                "current_priority": "C",
                "condition_changes": [
                    "Breakout lost",
                    "Volume confirmation lost",
                    "Consolidation lost",
                ],
            }
        ],
    }

    message = ChangeIntelligenceService.generate_summary(comparison)[0]["message"]
    assert "Breakout, volume confirmation and consolidation were lost." in message
