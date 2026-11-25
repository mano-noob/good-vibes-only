import pandas as pd
import pytest

from app.indicators.technical_indicators import TechnicalIndicators
from app.services.backtest_service import BacktestService
from app.services.market_regime_service import MarketRegimeService


def test_non_empty_trade_statistics_are_complete_and_net_of_costs():
    result = BacktestService.calculate_statistics(
        "TEST",
        [8.0, -6.0, 1.0],
        [
            {"gross_return_pct": 10.0, "return_pct": 8.0},
            {"gross_return_pct": -4.0, "return_pct": -6.0},
            {"gross_return_pct": 2.0, "return_pct": 1.0},
        ],
    )

    assert result["trades"] == 3
    assert result["wins"] == 2
    assert result["losses"] == 1
    assert result["win_rate"] == pytest.approx(66.67)
    assert result["gross_profit"] == pytest.approx(12.0)
    assert result["gross_loss"] == pytest.approx(4.0)
    assert result["net_profit"] == pytest.approx(9.0)
    assert result["net_loss"] == pytest.approx(6.0)
    assert result["profit_factor"] == pytest.approx(1.5)
    assert result["average_return"] == pytest.approx(1.0)
    assert result["expectancy"] == pytest.approx(1.0)
    assert result["total_return"] == pytest.approx(3.0)
    assert len(result["trade_log"]) == 3


def test_zero_trade_statistics_preserve_existing_empty_result_fields():
    result = BacktestService.calculate_statistics("TEST", [], [])

    assert result["trades"] == 0
    assert result["wins"] == 0
    assert result["losses"] == 0
    assert result["profit_factor"] is None
    assert result["average_return"] == 0
    assert result["total_return"] == 0


def test_execution_costs_apply_adverse_slippage_and_both_side_fees():
    result = BacktestService.calculate_execution_costs(
        100,
        110,
        {
            "brokerage_pct": 0.03,
            "transaction_cost_pct": 0.10,
            "slippage_bps": 10,
        },
    )

    assert result["entry_fill_price"] == pytest.approx(100.1)
    assert result["exit_fill_price"] == pytest.approx(109.89)
    assert result["brokerage_cost"] == pytest.approx((100.1 + 109.89) * 0.0003)
    assert result["transaction_cost"] == pytest.approx((100.1 + 109.89) * 0.001)
    assert result["slippage_cost"] == pytest.approx(0.21)
    assert result["net_profit_per_share"] < result["gross_profit_per_share"]
    assert result["net_return_pct"] < result["gross_return_pct"]
    entry_outlay = result["entry_fill_price"] + result["entry_fill_price"] * (0.0003 + 0.001)
    assert result["net_return_pct"] == pytest.approx(
        result["net_profit_per_share"] / entry_outlay * 100
    )


def test_profit_factor_is_undefined_when_there_are_no_losing_trades():
    result = BacktestService.calculate_statistics(
        "TEST",
        [5.0, 0.0],
        [
            {"gross_return_pct": 5.5, "return_pct": 5.0},
            {"gross_return_pct": 0.5, "return_pct": 0.0},
        ],
    )

    assert result["profit_factor"] is None


def test_breakeven_trade_is_not_counted_as_a_loss_or_average_loss():
    result = BacktestService.calculate_statistics(
        "TEST",
        [5.0, 0.0, -1.0],
        [
            {"gross_return_pct": 5.5, "return_pct": 5.0},
            {"gross_return_pct": 0.5, "return_pct": 0.0},
            {"gross_return_pct": -1.5, "return_pct": -1.0},
        ],
    )

    assert result["wins"] == 1
    assert result["losses"] == 1
    assert result["breakeven_trades"] == 1
    assert result["average_loss"] == 1.0


def test_default_backtest_cost_assumptions_are_configurable(monkeypatch):
    monkeypatch.setattr(
        "app.services.backtest_service.ConfigService.get",
        lambda key, default: {
            "backtest_brokerage_pct": 0.02,
            "backtest_transaction_cost_pct": 0.08,
            "backtest_slippage_bps": 3,
        }.get(key, default),
    )

    assert BacktestService.cost_assumptions() == {
        "brokerage_pct": 0.02,
        "transaction_cost_pct": 0.08,
        "slippage_bps": 3.0,
    }


def test_live_and_historical_regime_share_ema50_over_ema200_rule(monkeypatch):
    dates = pd.date_range("2025-01-01", periods=3, freq="D")
    market = pd.DataFrame({"Date": dates, "Close": [10.0, 9.0, 11.0]})
    monkeypatch.setattr(
        TechnicalIndicators,
        "calculate_ema50",
        staticmethod(lambda _df: pd.Series([10.0, 9.0, 11.0])),
    )
    monkeypatch.setattr(
        TechnicalIndicators,
        "calculate_ema200",
        staticmethod(lambda _df: pd.Series([9.0, 10.0, 10.0])),
    )

    historical = BacktestService._market_regimes_for_dates(market, dates)

    assert historical.tolist() == [True, False, True]
    assert MarketRegimeService.is_bullish_ema(10.0, 9.0) is True
    assert MarketRegimeService.is_bullish_ema(9.0, 10.0) is False


def test_historical_regime_unavailable_fails_safely():
    with pytest.raises(ValueError, match="Historical NIFTY data is unavailable"):
        BacktestService._market_regimes_for_dates(pd.DataFrame(), pd.date_range("2025-01-01", periods=1))


def test_historical_regime_without_stock_date_overlap_fails_safely(monkeypatch):
    market = pd.DataFrame({"Date": pd.date_range("2025-01-01", periods=2), "Close": [1.0, 2.0]})
    monkeypatch.setattr(
        TechnicalIndicators,
        "calculate_ema50",
        staticmethod(lambda _df: pd.Series([2.0, 3.0])),
    )
    monkeypatch.setattr(
        TechnicalIndicators,
        "calculate_ema200",
        staticmethod(lambda _df: pd.Series([1.0, 2.0])),
    )

    with pytest.raises(ValueError, match="does not overlap"):
        BacktestService._market_regimes_for_dates(
            market,
            pd.Series(pd.to_datetime(["2026-01-01"])),
        )


def _patch_single_symbol_history(monkeypatch, candles, tmp_path):
    row_count = len(next(iter(candles.values())))
    dates = pd.date_range("2025-01-01", periods=row_count, freq="D")
    frame = pd.DataFrame({"Date": dates, **candles})
    monkeypatch.setattr(BacktestService, "TRADE_LOG_DIR", tmp_path)
    monkeypatch.setattr(
        "app.services.backtest_service.MarketDataService.get_stock_data",
        staticmethod(lambda symbol, **_kwargs: frame.copy()),
    )
    for name, values in {
        "calculate_ema": [100.0] * len(frame),
        "calculate_rsi": [60.0] * len(frame),
        "calculate_atr": [2.0] * len(frame),
        "calculate_ema50": [101.0] * len(frame),
        "calculate_ema200": [100.0] * len(frame),
    }.items():
        monkeypatch.setattr(
            TechnicalIndicators,
            name,
            staticmethod(lambda _df, values=values: pd.Series(values)),
        )
    monkeypatch.setattr(
        BacktestService,
        "_market_regimes_for_dates",
        staticmethod(lambda _market, stock_dates: pd.Series([True] * len(stock_dates))),
    )
    signals = iter(["BUY", "NO SIGNAL"])
    monkeypatch.setattr(
        "app.services.backtest_service.BreakoutStrategy.generate_signal",
        lambda _sample: {"signal": next(signals, "NO SIGNAL")},
    )
    monkeypatch.setattr(BacktestService, "cost_assumptions", staticmethod(lambda: {
        "brokerage_pct": 0.0,
        "transaction_cost_pct": 0.0,
        "slippage_bps": 0.0,
    }))


def test_backtest_checks_stop_on_entry_candle(monkeypatch, tmp_path):
    count = 205
    candles = {
        "Open": [100.0] * count,
        "High": [101.0] * count,
        "Low": [99.0] * count,
        "Close": [100.0] * count,
        "Volume": [1000.0] * count,
    }
    candles["Low"][201] = 95.0
    _patch_single_symbol_history(monkeypatch, candles, tmp_path)

    result = BacktestService.run_backtest("TEST", max_hold_days=2)

    assert result["trades"] == 1
    assert result["trade_log"][0]["entry_date"] == "2025-07-21 00:00:00"
    assert result["trade_log"][0]["exit_date"] == "2025-07-21 00:00:00"
    assert result["trade_log"][0]["exit_price"] == 96.0
    assert "exit_reason" not in result["trade_log"][0]


def test_close_confirmed_breakeven_stop_applies_next_candle(monkeypatch, tmp_path):
    count = 205
    candles = {
        "Open": [100.0] * count,
        "High": [101.0] * count,
        "Low": [99.0] * count,
        "Close": [100.0] * count,
        "Volume": [1000.0] * count,
    }
    candles["High"][201] = 106.0
    candles["Low"][201] = 98.0
    candles["Close"][201] = 105.0
    candles["Low"][202] = 99.0
    _patch_single_symbol_history(monkeypatch, candles, tmp_path)

    result = BacktestService.run_backtest("TEST", max_hold_days=2)

    assert result["trades"] == 1
    assert result["trade_log"][0]["exit_date"] == "2025-07-22 00:00:00"
    assert result["trade_log"][0]["exit_price"] == 100.0


def test_stop_gap_uses_worse_opening_fill(monkeypatch, tmp_path):
    count = 205
    candles = {
        "Open": [100.0] * count,
        "High": [101.0] * count,
        "Low": [99.0] * count,
        "Close": [100.0] * count,
        "Volume": [1000.0] * count,
    }
    candles["Open"][202] = 90.0
    candles["Low"][202] = 89.0
    candles["Close"][202] = 90.0
    _patch_single_symbol_history(monkeypatch, candles, tmp_path)

    result = BacktestService.run_backtest("TEST", max_hold_days=2)

    assert result["trades"] == 1
    assert result["trade_log"][0]["exit_date"] == "2025-07-22 00:00:00"
    assert result["trade_log"][0]["exit_price"] == 90.0


def test_trade_log_persists_and_loads_existing_fields_and_derived_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(BacktestService, "TRADE_LOG_DIR", tmp_path)
    trade = {
        "entry_date": "2025-01-01 00:00:00",
        "exit_date": "2025-01-06 00:00:00",
        "entry_price": 101.0,
        "exit_price": 109.0,
        "reference_entry_price": 100.0,
        "reference_exit_price": 110.0,
        "gross_return_pct": 10.0,
        "return_pct": 7.5,
        "brokerage_cost_per_share": 0.1,
        "transaction_cost_per_share": 0.2,
        "slippage_cost_per_share": 2.0,
        "cost_assumptions": {
            "brokerage_pct": 0.03,
            "transaction_cost_pct": 0.10,
            "slippage_bps": 5.0,
        },
        "entry_market_regime": "Bullish",
        "exit_reason": "target",
    }

    path = BacktestService.persist_trade_log("TEST.NS", [trade], trade["cost_assumptions"])
    payload = BacktestService.load_trade_log(path)

    assert path.parent == tmp_path
    assert payload["symbol"] == "TEST.NS"
    assert payload["trade_count"] == 1
    saved_trade = payload["trades"][0]
    assert saved_trade["symbol"] == "TEST.NS"
    assert saved_trade["holding_days"] == 5
    assert saved_trade["entry_market_regime"] == "Bullish"
    assert saved_trade["exit_reason"] == "target"
    assert saved_trade["return_pct"] == 7.5
    assert saved_trade["brokerage_cost_per_share"] == 0.1


def test_trade_log_handles_invalid_dates_and_empty_results(tmp_path, monkeypatch):
    monkeypatch.setattr(BacktestService, "TRADE_LOG_DIR", tmp_path)

    path = BacktestService.persist_trade_log("TEST/UNSAFE", [{
        "entry_date": "unknown",
        "exit_date": "2025-01-01",
        "exit_reason": "other",
    }], {})
    payload = BacktestService.load_trade_log(path)

    assert path.parent == tmp_path
    assert "/" not in path.name
    assert payload["trade_count"] == 1
    assert payload["trades"][0]["holding_days"] is None
    assert payload["trades"][0]["symbol"] == "TEST/UNSAFE"

    empty_path = BacktestService.persist_trade_log("EMPTY", [], {})
    assert BacktestService.load_trade_log(empty_path)["trades"] == []