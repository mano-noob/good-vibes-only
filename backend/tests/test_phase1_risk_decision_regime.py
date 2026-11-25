import pandas as pd

from app.engines.decision_engine import DecisionEngine
from app.services.market_regime_service import MarketRegimeService
from app.services.market_data import MarketDataService
from app.indicators.technical_indicators import TechnicalIndicators
from app.services.risk_management_service import RiskManagementService
from app.services.ai_analysis_service import AIAnalysisService
from app.services.trading_service import TradingService


def test_risk_management_caps_quantity_to_available_cash():
    result = RiskManagementService.calculate_trade(
        entry_price=600,
        atr=1,
        available_cash=1000,
        settings={"risk_per_trade_pct": 2, "atr_multiplier": 2, "target_rr": 2.5},
    )

    assert result["position_size"] == 1
    assert result["capital_required"] <= 1000
    assert result["estimated_risk_amount"] == 2
    assert result["estimated_risk_amount"] <= result["risk_amount"]


def test_unknown_market_regime_blocks_new_buy(monkeypatch):
    monkeypatch.setattr(MarketRegimeService, "is_bull_market", staticmethod(lambda: None))

    assert MarketRegimeService.get_market_regime() == "Unknown"
    decision = DecisionEngine.decide("ABC", "BUY", False, "Unknown")
    assert decision["action"] == "WATCHLIST"


def test_market_regime_data_error_is_unavailable(monkeypatch):
    def raise_unavailable(*_args, **_kwargs):
        raise RuntimeError("data unavailable")

    monkeypatch.setattr(MarketDataService, "get_stock_data", raise_unavailable)

    assert MarketRegimeService.is_bull_market() is None
    assert MarketRegimeService.get_market_regime() == "Unknown"


def test_invalid_market_regime_values_are_unavailable(monkeypatch):
    monkeypatch.setattr(
        MarketDataService,
        "get_stock_data",
        staticmethod(lambda **_kwargs: pd.DataFrame({"Close": [1.0]})),
    )
    monkeypatch.setattr(
        TechnicalIndicators,
        "calculate_ema50",
        staticmethod(lambda _df: pd.Series([float("nan")])),
    )
    monkeypatch.setattr(
        TechnicalIndicators,
        "calculate_ema200",
        staticmethod(lambda _df: pd.Series([1.0])),
    )

    assert MarketRegimeService.is_bull_market() is None


def test_existing_position_exit_condition_takes_priority():
    decision = DecisionEngine.decide(
        "ABC", "BUY", True, "Bearish", exit_reason="Price below EMA200"
    )

    assert decision == {"action": "EXIT", "reason": "Price below EMA200"}


def test_buy_analysis_does_not_call_ai(monkeypatch):
    monkeypatch.setattr(
        TechnicalIndicators,
        "calculate_ema",
        staticmethod(lambda _df: pd.Series([100.0])),
    )
    monkeypatch.setattr(
        TechnicalIndicators,
        "calculate_atr",
        staticmethod(lambda _df: pd.Series([2.0])),
    )
    monkeypatch.setattr(
        TechnicalIndicators,
        "calculate_rsi",
        staticmethod(lambda _df: pd.Series([60.0])),
    )
    monkeypatch.setattr(
        TechnicalIndicators,
        "calculate_ema50",
        staticmethod(lambda _df: pd.Series([99.0])),
    )
    monkeypatch.setattr(
        TechnicalIndicators,
        "calculate_ema200",
        staticmethod(lambda _df: pd.Series([98.0])),
    )
    monkeypatch.setattr(
        "app.services.trading_service.BreakoutStrategy.generate_signal",
        lambda _df: {"signal": "BUY", "reason": "existing rule", "diagnostics": {}},
    )

    def fail_if_called(_data):
        raise AssertionError("AI analysis must not run")

    monkeypatch.setattr(AIAnalysisService, "generate_trade_analysis", staticmethod(fail_if_called))
    data = pd.DataFrame(
        {"Close": [101.0], "High": [102.0], "Low": [100.0], "Volume": [1000]}
    )

    result = TradingService.analyze_stock("ABC", df=data)

    assert result["signal"]["signal"] == "BUY"
    assert result["ai_analysis"] is None