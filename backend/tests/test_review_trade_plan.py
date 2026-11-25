import copy

from app.core.config_service import ConfigService
from app.core.review_history import ReviewHistory
from app.engines.decision_engine import DecisionEngine
from app.services.alert_service import AlertService
from app.services.market_regime_service import MarketRegimeService
from app.services.portfolio_service import PortfolioService
from app.services.position_service import PositionService
from app.services.relative_strength_service import RelativeStrengthService
from app.services.review_comparison_service import ReviewComparisonService
from app.services.review_service import ReviewService
from app.services.review_summary_service import ReviewSummaryService
from app.services.trading_service import TradingService


def _configure_review(monkeypatch, portfolio, candidates, max_positions=8):
    monkeypatch.setattr(
        MarketRegimeService,
        "get_market_regime",
        staticmethod(lambda: "Bullish"),
    )
    monkeypatch.setattr(
        RelativeStrengthService,
        "get_rankings",
        staticmethod(lambda return_data=False: candidates),
    )
    monkeypatch.setattr(PortfolioService, "load", staticmethod(lambda: portfolio))
    monkeypatch.setattr(
        PortfolioService,
        "get_positions",
        staticmethod(lambda: portfolio["positions"]),
    )
    monkeypatch.setattr(
        PortfolioService,
        "is_owned",
        staticmethod(lambda symbol: any(p["symbol"] == symbol for p in portfolio["positions"])),
    )
    monkeypatch.setattr(
        PortfolioService,
        "get_position",
        staticmethod(
            lambda symbol: next(
                (p for p in portfolio["positions"] if p["symbol"] == symbol),
                None,
            )
        ),
    )
    monkeypatch.setattr(PortfolioService, "save", staticmethod(lambda _portfolio: None))
    monkeypatch.setattr(
        ConfigService,
        "get",
        staticmethod(
            lambda key, default=None: {
                "relative_strength_count": len(candidates),
                "watchlist_size": 10,
                "max_positions": max_positions,
            }.get(key, default)
        ),
    )
    monkeypatch.setattr(
        ConfigService,
        "all",
        staticmethod(
            lambda: {
                "risk_per_trade_pct": 2,
                "atr_multiplier": 2,
                "target_rr": 2.5,
            }
        ),
    )
    monkeypatch.setattr(ReviewHistory, "load", staticmethod(lambda: []))
    monkeypatch.setattr(ReviewHistory, "append", staticmethod(lambda _review: None))
    monkeypatch.setattr(
        ReviewComparisonService,
        "compare",
        staticmethod(lambda _previous, _current: {}),
    )
    monkeypatch.setattr(
        ReviewSummaryService,
        "generate",
        staticmethod(lambda _review: {}),
    )
    monkeypatch.setattr(AlertService, "generate", staticmethod(lambda _review: []))

    analyses = {
        candidate["symbol"]: {
            "symbol": candidate["symbol"],
            "close_price": candidate["price"],
            "atr": candidate.get("atr", 1),
            "ema20": candidate.get("ema20", candidate["price"] - 1),
            "ema50": candidate.get("ema50", candidate["price"] - 1),
            "ema200": candidate.get("ema200", candidate["price"] - 2),
            "rsi": 60,
            "signal": {
                "signal": candidate.get("signal", "BUY"),
                "reason": candidate.get("signal_reason", "Existing breakout rule"),
                "diagnostics": {"trend_confirmation": True},
            },
            "readiness_score": 100,
            "priority": "A",
            "explanation": "Existing test signal",
        }
        for candidate in candidates
    }
    monkeypatch.setattr(
        TradingService,
        "analyze_stock",
        staticmethod(lambda symbol, df=None: copy.deepcopy(analyses[symbol])),
    )
    monkeypatch.setattr(
        DecisionEngine,
        "is_exit_action",
        staticmethod(DecisionEngine.is_exit_action),
    )


def _candidate(symbol, price, score):
    return {"symbol": symbol, "score": score, "df": None, "price": price}


def test_review_aggregates_buy_allocations_without_mutating_portfolio(monkeypatch):
    portfolio = {"cash": 100, "positions": []}
    candidates = [_candidate("AAA", 60, 20), _candidate("BBB", 60, 10)]
    _configure_review(monkeypatch, portfolio, candidates)

    review = ReviewService.generate_review()

    assert [item["symbol"] for item in review["buy"]] == ["AAA"]
    assert review["watchlist"][0]["decision"]["action"] == "WATCHLIST"
    assert sum(
        item["proposed_capital_allocation"] for item in review["trade_plan"]
    ) <= portfolio["cash"]
    assert review["trade_plan"][0]["quantity"] == 1
    assert review["trade_plan"][0]["stop_loss"] == 58
    assert review["trade_plan"][0]["target"] == 65
    assert portfolio == {"cash": 100, "positions": []}


def test_review_enforces_maximum_position_count(monkeypatch):
    portfolio = {"cash": 100, "positions": []}
    candidates = [_candidate("AAA", 20, 20), _candidate("BBB", 20, 10)]
    _configure_review(monkeypatch, portfolio, candidates, max_positions=1)

    review = ReviewService.generate_review()

    assert [item["symbol"] for item in review["buy"]] == ["AAA"]
    assert review["watchlist"][0]["decision"]["reason"] == (
        "Maximum open-position limit reached"
    )


def test_review_emits_exit_for_existing_stop_condition_without_closing_position(monkeypatch):
    position = {
        "symbol": "AAA",
        "quantity": 5,
        "entry_price": 100,
        "entry_date": "2026-01-01",
        "initial_stop": 90,
        "current_stop": 90,
        "highest_price": 120,
    }
    portfolio = {"cash": 500, "positions": [position]}
    candidate = _candidate("AAA", 105, 20)
    candidate.update({"signal": "NO SIGNAL", "ema200": 110, "atr": 1})
    _configure_review(monkeypatch, portfolio, [candidate])

    review = ReviewService.generate_review()

    assert review["exit"][0]["decision"] == {
        "action": "EXIT",
        "reason": "Price below EMA200",
    }
    assert review["trade_plan"][0]["decision"] == "EXIT"
    assert review["trade_plan"][0]["quantity"] == 5
    assert review["portfolio_summary"]["market_value"] == 525
    assert review["portfolio_summary"]["unrealized_pnl"] == 25
    assert position in portfolio["positions"]


def test_review_emits_exit_for_trailing_stop_breach(monkeypatch):
    position = {
        "symbol": "AAA",
        "quantity": 5,
        "entry_price": 100,
        "entry_date": "2026-01-01",
        "initial_stop": 90,
        "current_stop": 110,
        "highest_price": 120,
    }
    portfolio = {"cash": 500, "positions": [position]}
    candidate = _candidate("AAA", 105, 20)
    candidate.update({"signal": "NO SIGNAL", "ema200": 80, "atr": 1})
    _configure_review(monkeypatch, portfolio, [candidate])

    review = ReviewService.generate_review()

    assert review["exit"][0]["decision"] == {
        "action": "EXIT",
        "reason": "Price below current trailing stop",
    }


def test_review_persists_only_monotonic_trailing_stop(monkeypatch):
    position = {
        "symbol": "AAA",
        "quantity": 1,
        "entry_price": 100,
        "entry_date": "2026-01-01",
        "initial_stop": 90,
        "current_stop": 110,
        "highest_price": 120,
    }
    portfolio = {"cash": 500, "positions": [position]}
    candidate = _candidate("AAA", 125, 20)
    candidate.update({"signal": "NO SIGNAL", "ema200": 80, "atr": 10})
    _configure_review(monkeypatch, portfolio, [candidate])
    saved = {}
    monkeypatch.setattr(
        PortfolioService,
        "save",
        staticmethod(lambda value: saved.update(copy.deepcopy(value))),
    )

    ReviewService.generate_review()

    assert saved["positions"][0]["current_stop"] >= 110