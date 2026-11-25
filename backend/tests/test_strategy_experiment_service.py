import pandas as pd
import pytest

from app.core.config_service import ConfigService
from app.core.watchlist import NIFTY_100
from app.services.strategy_experiment_service import StrategyExperimentService
from app.strategies.breakout_strategy import BreakoutStrategy


def _history(dates, prices=None):
    prices = prices or [100.0] * len(dates)
    return pd.DataFrame({
        "Date": dates,
        "Open": prices,
        "High": [price + 1 for price in prices],
        "Low": [price - 1 for price in prices],
        "Close": prices,
        "Volume": [1000.0] * len(prices),
    })


def test_alignment_preserves_native_dates_and_uses_union_calendar():
    dates = pd.date_range("2020-01-01", periods=400, freq="B")
    stock_a = _history(dates)
    stock_b = _history(dates.delete(5))
    benchmark = _history(dates.delete(10))

    aligned, aligned_benchmark, common_dates = StrategyExperimentService.align_prepared_data(
        {"AAA": stock_a, "BBB": stock_b}, benchmark
    )
    split = StrategyExperimentService.split_dates(common_dates)

    assert len(common_dates) == 400
    assert len(aligned["AAA"]) == 400
    assert len(aligned["BBB"]) == 399
    assert len(aligned_benchmark) == 399
    assert pd.to_datetime(aligned["AAA"].iloc[:, 0]).dt.normalize().tolist() == dates.tolist()
    assert pd.to_datetime(aligned["BBB"].iloc[:, 0]).dt.normalize().tolist() == stock_b["Date"].tolist()
    assert pd.to_datetime(aligned_benchmark.iloc[:, 0]).dt.normalize().tolist() == benchmark["Date"].tolist()
    assert dates[5] not in pd.to_datetime(aligned["BBB"].iloc[:, 0]).dt.normalize().tolist()
    assert common_dates[split["split_index"] - 1] < common_dates[split["split_index"]]
    assert split["training_end"] < split["test_start"]


def test_explicit_split_date_must_be_in_aligned_data():
    dates = pd.date_range("2020-01-01", periods=400, freq="B")
    stock = _history(dates)
    benchmark = _history(dates)

    with pytest.raises(ValueError, match="must exist on the benchmark trading calendar"):
        StrategyExperimentService.run_experiment(
            {"AAA": stock}, benchmark, split_date="2030-01-01"
        )


def test_benchmark_return_uses_exact_test_boundary_dates_when_available():
    dates = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"])
    benchmark = pd.DataFrame({"Date": dates, "Close": [100.0, 105.0, 110.0]})

    result = StrategyExperimentService.benchmark_return_on_dates(
        benchmark, "2024-01-03", "2024-01-04"
    )

    assert result["actual_test_start"] == "2024-01-03T00:00:00"
    assert result["actual_test_end"] == "2024-01-04T00:00:00"
    assert result["test_return_pct"] == pytest.approx(round((110 / 105 - 1) * 100, 4))


def test_benchmark_return_uses_last_close_before_missing_start_boundary():
    benchmark = pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-02", "2024-01-04", "2024-01-05"]),
        "Close": [100.0, 108.0, 110.0],
    })

    result = StrategyExperimentService.benchmark_return_on_dates(
        benchmark, "2024-01-03", "2024-01-05"
    )

    assert result["actual_test_start"] == "2024-01-02T00:00:00"
    assert result["actual_test_end"] == "2024-01-05T00:00:00"
    assert result["test_start_close"] == 100.0


def test_benchmark_return_uses_last_close_before_missing_end_boundary():
    benchmark = pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-02", "2024-01-04"]),
        "Close": [100.0, 108.0],
    })

    result = StrategyExperimentService.benchmark_return_on_dates(
        benchmark, "2024-01-02", "2024-01-05"
    )

    assert result["actual_test_start"] == "2024-01-02T00:00:00"
    assert result["actual_test_end"] == "2024-01-04T00:00:00"
    assert result["test_end_close"] == 108.0


def test_benchmark_return_fails_if_start_has_no_prior_valid_close():
    benchmark = pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-02", "2024-01-04"]),
        "Close": [100.0, 108.0],
    })

    with pytest.raises(ValueError, match="No valid benchmark close exists on or before test start"):
        StrategyExperimentService.benchmark_return_on_dates(
            benchmark, "2024-01-01", "2024-01-05"
        )


def test_benchmark_return_rejects_reversed_test_date_range():
    benchmark = pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-02", "2024-01-04"]),
        "Close": [100.0, 108.0],
    })

    with pytest.raises(ValueError, match="must not be after end date"):
        StrategyExperimentService.benchmark_return_on_dates(
            benchmark, "2024-01-05", "2024-01-04"
        )


def test_alignment_rejects_missing_ohlcv_values():
    dates = pd.date_range("2020-01-01", periods=400, freq="B")
    stock = _history(dates)
    stock.loc[10, "Volume"] = float("nan")

    with pytest.raises(ValueError, match="missing or non-finite OHLCV"):
        StrategyExperimentService.align_prepared_data({"AAA": stock}, _history(dates))


def test_other_symbols_missing_session_does_not_change_stock_indicators_or_signal():
    dates = pd.date_range("2020-01-01", periods=400, freq="B")
    prices = [100.0 + index * 0.1 + (index % 7) * 0.03 for index in range(len(dates))]
    stock_a = _history(dates, prices)
    stock_b = _history(dates.delete(260))
    benchmark = _history(dates)

    alone, _, _ = StrategyExperimentService.align_prepared_data({"AAA": stock_a}, benchmark)
    together, _, _ = StrategyExperimentService.align_prepared_data(
        {"AAA": stock_a, "BBB": stock_b}, benchmark
    )
    alone_a = StrategyExperimentService._prepare_frames(alone)["AAA"]
    together_a = StrategyExperimentService._prepare_frames(together)["AAA"]
    native_date = dates[300]
    alone_index = alone_a.index[pd.to_datetime(alone_a.iloc[:, 0]).dt.normalize() == native_date][0]
    together_index = together_a.index[pd.to_datetime(together_a.iloc[:, 0]).dt.normalize() == native_date][0]

    for column in ("EMA20", "RSI", "ATR", "EMA50", "EMA200"):
        assert alone_a[column].iloc[alone_index] == pytest.approx(
            together_a[column].iloc[together_index]
        )
    alone_signal = BreakoutStrategy.generate_signal(alone_a.iloc[:alone_index + 1])
    together_signal = BreakoutStrategy.generate_signal(together_a.iloc[:together_index + 1])
    assert alone_signal == together_signal


def test_fixed_breakout_distance_exact_boundaries():
    baseline = StrategyExperimentService.VARIANTS["baseline"]
    breakout_1_5 = StrategyExperimentService.VARIANTS["breakout_1_5"]
    breakout_2 = StrategyExperimentService.VARIANTS["breakout_2"]
    dates = pd.date_range("2024-01-01", periods=60, freq="B")
    benchmark = pd.DataFrame({"Date": dates, "Close": [100.0] * 60})

    frame = pd.DataFrame({
        "Date": dates,
        "Close": [100.0] * 59 + [101.5],
        "High": [100.0] * 59 + [101.5],
        "EMA200": [90.0] * 60,
        "Volume": [100.0] * 60,
    })
    assert StrategyExperimentService.variant_passes(frame, 59, benchmark, baseline)
    assert StrategyExperimentService.variant_passes(frame, 59, benchmark, breakout_1_5)

    frame.loc[59, "Close"] = 101.499
    frame.loc[59, "High"] = 101.499
    assert not StrategyExperimentService.variant_passes(frame, 59, benchmark, breakout_1_5)

    frame.loc[59, "Close"] = 102.0
    frame.loc[59, "High"] = 102.0
    assert StrategyExperimentService.variant_passes(frame, 59, benchmark, breakout_2)


def test_relative_volume_excludes_signal_day():
    volumes = [10.0] * 20 + [20.0]
    frame = pd.DataFrame({
        "Open": [100.0] * 21,
        "High": [101.0] * 21,
        "Low": [99.0] * 21,
        "Close": [100.0] * 21,
        "Volume": volumes,
    })

    assert StrategyExperimentService.relative_volume_at(frame, 20) == pytest.approx(2.0)
    assert StrategyExperimentService.relative_volume_at(frame, 19) is None


def test_relative_strength_is_stock_minus_nifty_at_signal_date_and_ignores_future():
    stock_dates = pd.date_range("2024-01-01", periods=65, freq="B")
    stock = pd.DataFrame({
        "Date": stock_dates,
        "Close": [100.0] * 64 + [130.0],
    })
    benchmark_dates = pd.date_range("2024-01-01", periods=65, freq="B")
    benchmark_close = [100.0] * 63 + [105.0] * 2
    benchmark = pd.DataFrame({
        "Date": benchmark_dates,
        "Close": benchmark_close,
    })
    future = pd.DataFrame({
        "Date": pd.to_datetime(["2024-05-01"]),
        "Close": [200.0],
    })
    benchmark = pd.concat([benchmark, future], ignore_index=True)

    stock_index = 64
    result = StrategyExperimentService.relative_strength_vs_nifty(stock, stock_index, benchmark)

    stock_return = 30.0
    benchmark_return = 5.0
    assert result == pytest.approx(stock_return - benchmark_return)


def test_relative_strength_rejects_missing_future_and_stale_benchmark():
    stock = pd.DataFrame({
        "Date": pd.date_range("2024-01-01", periods=65, freq="B"),
        "Close": [100.0] * 64 + [130.0],
    })
    future_only = pd.DataFrame({
        "Date": pd.to_datetime(["2025-01-01"]),
        "Close": [100.0],
    })
    stale = pd.DataFrame({
        "Date": pd.date_range("2023-01-01", periods=65, freq="B"),
        "Close": [100.0] * 65,
    })

    assert StrategyExperimentService.relative_strength_vs_nifty(stock, 64, future_only) is None
    assert StrategyExperimentService.relative_strength_vs_nifty(stock, 64, stale) is None


def test_variant_filter_combined_requires_all_three_filters(monkeypatch):
    dates = pd.date_range("2024-01-01", periods=70, freq="B")
    frame = pd.DataFrame({
        "Date": dates,
        "Open": [100.0] * 70,
        "High": [102.0] * 70,
        "Low": [99.0] * 70,
        "Close": [102.0] * 70,
        "Volume": [20.0] * 69 + [40.0],
        "EMA200": [90.0] * 70,
    })
    benchmark = pd.DataFrame({
        "Date": dates,
        "Close": [100.0] * 70,
    })

    monkeypatch.setattr(
        StrategyExperimentService,
        "relative_strength_vs_nifty",
        staticmethod(lambda *_args, **_kwargs: 6.0),
    )
    combined = StrategyExperimentService.VARIANTS["combined"]
    frame.loc[:68, "High"] = 100.0

    assert StrategyExperimentService.variant_passes(frame, 69, benchmark, combined)


def test_thresholds_are_additional_to_existing_baseline_conditions():
    assert StrategyExperimentService.passes_thresholds(102, 100, 90)
    assert StrategyExperimentService.passes_thresholds(102, 100, 90, 2.0, 13.0)
    assert not StrategyExperimentService.passes_thresholds(101, 100, 90, 1.5, None)
    assert not StrategyExperimentService.passes_thresholds(102, 100, 91, None, 12.5)
    assert not StrategyExperimentService.passes_thresholds(102, 0, 90)


def test_fee_aware_risk_sizing_never_spends_more_than_cash():
    assumptions = {"brokerage_pct": 0.03, "transaction_cost_pct": 0.10, "slippage_bps": 5.0}
    settings = {"risk_per_trade_pct": 100, "atr_multiplier": 2, "target_rr": 2}

    order = StrategyExperimentService.size_order(100, 1, 250, assumptions, settings)

    assert order["shares"] > 0
    assert order["entry_cost"] <= 250
    assert order["entry_cost"] == pytest.approx(order["shares"] * order["entry_fill"] * 1.0013)


def test_equity_metrics_calculate_net_return_expectancy_profit_factor_and_drawdown():
    curve = [
        {"date": "2024-01-02", "equity": 1000, "exposure_pct": 0, "cash_utilization_pct": 0},
        {"date": "2024-02-02", "equity": 1100, "exposure_pct": 25, "cash_utilization_pct": 27.5},
        {"date": "2024-03-02", "equity": 880, "exposure_pct": 50, "cash_utilization_pct": 44},
        {"date": "2024-04-02", "equity": 1200, "exposure_pct": 10, "cash_utilization_pct": 12},
    ]
    trades = [
        {"net_pnl": 100},
        {"net_pnl": -50},
        {"net_pnl": 150},
    ]

    result = StrategyExperimentService._metric_summary(curve, trades, 1000, 2)

    assert result["trade_count"] == 3
    assert result["win_rate_pct"] == pytest.approx(66.6667)
    assert result["net_expectancy"] == pytest.approx(200 / 3)
    assert result["profit_factor"] == pytest.approx(5.0)
    assert result["net_return_pct"] == pytest.approx(20.0)
    assert result["maximum_drawdown_pct"] == pytest.approx(-20.0)
    assert result["average_exposure_pct"] == pytest.approx(21.25)
    assert result["maximum_exposure_pct"] == pytest.approx(50.0)
    assert result["average_cash_utilization_pct_of_starting_capital"] == pytest.approx(20.875)
    assert result["maximum_cash_utilization_pct_of_starting_capital"] == pytest.approx(44.0)
    assert result["max_concurrent_positions"] == 2
    assert result["quarterly_summaries"][0]["quarter"] == "2024-Q1"
    assert result["quarterly_summaries"][0]["return_pct"] == pytest.approx(-12.0)
    assert result["quarterly_summaries"][0]["maximum_drawdown_pct"] == pytest.approx(-20.0)
    assert result["quarterly_summaries"][1]["quarter"] == "2024-Q2"


def test_simulation_enforces_position_cap_and_alphabetical_tie_break(monkeypatch):
    dates = pd.date_range("2020-01-01", periods=300, freq="B")
    stock_a = _history(dates)
    stock_b = _history(dates)
    benchmark = _history(dates, [100.0 + index for index in range(len(dates))])
    aligned, aligned_benchmark, _ = StrategyExperimentService.align_prepared_data(
        {"BBB": stock_b, "AAA": stock_a}, benchmark
    )
    frames = StrategyExperimentService._prepare_frames(aligned)
    monkeypatch.setattr(
        ConfigService,
        "all",
        staticmethod(lambda: {
            "capital": 1000,
            "risk_per_trade_pct": 2,
            "max_positions": 1,
            "relative_strength_3m_lookback": 63,
            "relative_strength_6m_lookback": 126,
            "relative_strength_12m_lookback": 252,
            "relative_strength_3m_weight": 0.3,
            "relative_strength_6m_weight": 0.3,
            "relative_strength_12m_weight": 0.4,
        }),
    )
    monkeypatch.setattr(ConfigService, "get", staticmethod(lambda _key, default=None: default))
    monkeypatch.setattr(
        StrategyExperimentService,
        "_signal_inputs_valid",
        staticmethod(lambda *_args, **_kwargs: True),
    )
    monkeypatch.setattr(
        BreakoutStrategy,
        "generate_signal",
        staticmethod(lambda _sample: {"signal": "BUY"}),
    )

    result = StrategyExperimentService._simulate_period(
        frames,
        aligned_benchmark,
        [True] * len(aligned_benchmark),
        252,
        len(dates),
        1000,
    )

    assert result["max_concurrent_positions"] == 1
    assert result["trade_count"] == 1
    assert result["trades"][0]["symbol"] == "AAA"
    assert result["per_stock_attribution"]["AAA"]["completed_trades"] == 1
    assert result["equity_curve"][-1]["cash"] >= 0
    assert result["equity_curve"][-1]["invested_market_value"] >= 0
    assert result["equity_curve"][-1]["exposure_pct"] >= 0
    assert result["ending_equity"] <= 1000


@pytest.mark.parametrize(
    ("exit_kind", "expected_reason", "pnl_is_positive"),
    [("stop", "stop-loss", False), ("target", "target", True)],
)
def test_simulator_checks_each_native_stock_bar_across_missing_union_session(
    monkeypatch, exit_kind, expected_reason, pnl_is_positive
):
    dates = pd.date_range("2020-01-01", periods=300, freq="B")
    prices = [100.0] * len(dates)
    frame = _history(dates, prices)
    if exit_kind == "stop":
        frame.loc[255, "Low"] = 95.0
    else:
        frame.loc[255, "High"] = 109.0
        frame.loc[255, "Low"] = 97.0
    stock = frame.drop(index=254).reset_index(drop=True)
    benchmark = _history(dates, [100.0 + index for index in range(len(dates))])
    aligned, aligned_benchmark, calendar = StrategyExperimentService.align_prepared_data(
        {"AAA": stock}, benchmark
    )
    frames = StrategyExperimentService._prepare_frames(aligned)

    monkeypatch.setattr(
        ConfigService,
        "all",
        staticmethod(lambda: {
            "capital": 1000,
            "risk_per_trade_pct": 2,
            "max_positions": 1,
            "relative_strength_3m_lookback": 63,
            "relative_strength_6m_lookback": 126,
            "relative_strength_12m_lookback": 252,
            "relative_strength_3m_weight": 0.3,
            "relative_strength_6m_weight": 0.3,
            "relative_strength_12m_weight": 0.4,
        }),
    )
    monkeypatch.setattr(ConfigService, "get", staticmethod(lambda _key, default=None: default))
    monkeypatch.setattr(
        StrategyExperimentService,
        "_signal_inputs_valid",
        staticmethod(lambda *_args, **_kwargs: True),
    )
    monkeypatch.setattr(
        BreakoutStrategy,
        "generate_signal",
        staticmethod(lambda sample: {"signal": "BUY" if len(sample) == 253 else "NO SIGNAL"}),
    )

    result = StrategyExperimentService._simulate_period(
        frames,
        aligned_benchmark,
        [True] * len(aligned_benchmark),
        252,
        len(calendar),
        1000,
    )

    assert len(calendar) == len(dates)
    assert dates[254] not in pd.to_datetime(aligned["AAA"].iloc[:, 0]).dt.normalize().tolist()
    assert result["trade_count"] == 1
    assert result["trades"][0]["exit_reason"] == expected_reason
    assert result["trades"][0]["exit_date"] == str(dates[255])
    gap_valuation = next(
        point for point in result["equity_curve"]
        if pd.Timestamp(point["date"]).normalize() == dates[254]
    )
    assert gap_valuation["invested_market_value"] == pytest.approx(
        result["trades"][0]["shares"] * 100.0
    )
    if pnl_is_positive:
        assert result["trades"][0]["net_pnl"] > 0
    else:
        assert result["trades"][0]["net_pnl"] < 0
    assert result["trades"][0]["shares"] > 0


def test_end_of_test_open_position_is_liquidated_with_costs(monkeypatch):
    dates = pd.date_range("2020-01-01", periods=300, freq="B")
    frame = _history(dates)
    frame.loc[254, "Close"] = 110.0
    frame.loc[254, "High"] = 107.0
    benchmark = _history(dates, [100.0 + index for index in range(len(dates))])
    aligned, aligned_benchmark, calendar = StrategyExperimentService.align_prepared_data(
        {"AAA": frame}, benchmark
    )
    frames = StrategyExperimentService._prepare_frames(aligned)

    monkeypatch.setattr(
        ConfigService,
        "all",
        staticmethod(lambda: {
            "capital": 1000,
            "risk_per_trade_pct": 2,
            "max_positions": 1,
            "relative_strength_3m_lookback": 63,
            "relative_strength_6m_lookback": 126,
            "relative_strength_12m_lookback": 252,
            "relative_strength_3m_weight": 0.3,
            "relative_strength_6m_weight": 0.3,
            "relative_strength_12m_weight": 0.4,
        }),
    )
    monkeypatch.setattr(ConfigService, "get", staticmethod(lambda _key, default=None: default))
    monkeypatch.setattr(StrategyExperimentService, "_signal_inputs_valid", staticmethod(lambda *_args, **_kwargs: True))
    monkeypatch.setattr(BreakoutStrategy, "generate_signal", staticmethod(lambda sample: {"signal": "BUY" if len(sample) == 253 else "NO SIGNAL"}))

    result = StrategyExperimentService._simulate_period(
        frames,
        aligned_benchmark,
        [True] * len(aligned_benchmark),
        252,
        255,
        1000,
        require_full_holding_window=False,
    )

    final_row = result["equity_curve"][-1]
    attribution = result["per_stock_attribution"]["AAA"]
    assert result["trade_count"] == 0
    assert attribution["open_shares"] > 0
    assert final_row["equity"] < 1000 + attribution["open_shares"] * 110.0
    assert attribution["ending_market_value"] < attribution["open_shares"] * 110.0


def test_fixed_six_variants_use_independent_actual_simulator_state(monkeypatch):
    dates = pd.date_range("2020-01-01", periods=400, freq="B")
    stock = _history(dates)
    benchmark = _history(dates, [100.0 + index for index in range(len(dates))])
    aligned, aligned_benchmark, _ = StrategyExperimentService.align_prepared_data(
        {"AAA": stock}, benchmark
    )
    frames = StrategyExperimentService._prepare_frames(aligned)

    monkeypatch.setattr(ConfigService, "get", staticmethod(lambda _key, default=None: default))
    monkeypatch.setattr(ConfigService, "all", staticmethod(lambda: {
        "capital": 100000,
        "risk_per_trade_pct": 2,
        "atr_multiplier": 2,
        "target_rr": 2,
        "max_positions": 8,
        "breakout_lookback": 55,
        "volume_lookback": 20,
    }))
    monkeypatch.setattr(StrategyExperimentService, "_signal_inputs_valid", staticmethod(lambda *_args, **_kwargs: True))
    monkeypatch.setattr(BreakoutStrategy, "generate_signal", staticmethod(lambda _sample: {"signal": "BUY"}))

    regimes = [True] * len(aligned_benchmark)
    baseline = StrategyExperimentService._simulate_period(
        frames, aligned_benchmark, regimes, 252, len(dates), 100000,
        variant=StrategyExperimentService.VARIANTS["baseline"],
        require_full_holding_window=False,
    )
    combined = StrategyExperimentService._simulate_period(
        frames, aligned_benchmark, regimes, 252, len(dates), 100000,
        variant=StrategyExperimentService.VARIANTS["combined"],
        require_full_holding_window=False,
    )

    assert set(baseline) == set(combined)
    assert baseline["ending_equity"] >= 0
    assert combined["ending_equity"] >= 0


def test_fixed_six_variants_use_identical_test_dates(monkeypatch):
    dates = pd.date_range("2020-01-01", periods=400, freq="B")
    stock = _history(dates)
    benchmark = _history(dates, [100 + index for index in range(len(dates))])
    calls = []

    def fake_simulate(_frames, _benchmark, _regimes, start, end, _capital, variant=None, require_full_holding_window=True):
        calls.append((start, end, variant, require_full_holding_window))
        return {
            "trade_count": 1,
            "net_expectancy": 1.0,
            "net_return_pct": 1.0,
            "win_rate_pct": 100.0,
            "profit_factor": None,
            "maximum_drawdown_pct": 0.0,
            "ending_equity": 101000.0,
            "trades": [],
            "equity_curve": [],
            "max_concurrent_positions": 1,
        }

    monkeypatch.setattr(StrategyExperimentService, "_simulate_period", staticmethod(fake_simulate))
    monkeypatch.setattr(ConfigService, "get", staticmethod(lambda _key, default=None: default))
    result = StrategyExperimentService.run_experiment({"AAA": stock}, benchmark)

    split_index = result["periods"]["split_index"]
    assert set(result["test_results"]) == set(StrategyExperimentService.VARIANTS)
    test_calls = [call for call in calls if call[0] == split_index]
    assert len(test_calls) == 6
    assert all(call[1] == len(dates) for call in test_calls)
    assert all(call[3] is False for call in test_calls)
    assert {call[2]["name"] for call in test_calls} == {
        "Baseline",
        "Breakout 1.5%",
        "Breakout 2%",
        "Breakout + Volume",
        "Breakout + Relative Strength",
        "Combined",
    }
    assert "selected_thresholds" not in result
    assert result["benchmark"]["test_return_pct"] == pytest.approx(
        (float(benchmark["Close"].iloc[-1]) / float(benchmark["Close"].iloc[split_index]) - 1) * 100
    )


def test_fixed_variants_have_independent_state(monkeypatch):
    dates = pd.date_range("2020-01-01", periods=400, freq="B")
    stock = _history(dates)
    benchmark = _history(dates, [100.0 + index for index in range(len(dates))])
    variant_keys = []

    def fake_simulate(_frames, _benchmark, _regimes, start, end, _capital, variant=None, require_full_holding_window=True):
        state = {"cash": 1000.0, "positions": {}, "equity_curve": []}
        variant_keys.append(variant["name"] if variant else "Baseline")
        return {
            "trade_count": 0,
            "net_expectancy": 0.0,
            "net_return_pct": 0.0,
            "win_rate_pct": 0.0,
            "profit_factor": None,
            "maximum_drawdown_pct": 0.0,
            "ending_equity": 1000.0,
            "trades": [],
            "equity_curve": [],
            "max_concurrent_positions": 0,
        }

    monkeypatch.setattr(StrategyExperimentService, "_simulate_period", staticmethod(fake_simulate))
    monkeypatch.setattr(ConfigService, "get", staticmethod(lambda _key, default=None: default))
    result = StrategyExperimentService.run_experiment({"AAA": stock}, benchmark)

    assert len(variant_keys) == 6
    assert len(set(variant_keys)) == 6
    assert set(result["test_results"]) == set(StrategyExperimentService.VARIANTS)


def test_static_nifty100_subset_is_labeled_exploratory(monkeypatch):
    dates = pd.date_range("2020-01-01", periods=400, freq="B")
    frame = _history(dates)

    def no_candidates(*_args, **_kwargs):
        return {
            "trade_count": 0,
            "net_expectancy": 0.0,
            "net_return_pct": 0.0,
            "win_rate_pct": 0.0,
            "profit_factor": None,
            "maximum_drawdown_pct": 0.0,
            "ending_equity": 100000.0,
            "trades": [],
            "equity_curve": [],
            "max_concurrent_positions": 0,
        }

    monkeypatch.setattr(StrategyExperimentService, "_simulate_period", staticmethod(no_candidates))
    monkeypatch.setattr(ConfigService, "get", staticmethod(lambda _key, default=None: default))

    result = StrategyExperimentService.run_experiment({NIFTY_100[0]: frame}, frame)

    assert result["universe_metadata"]["source"] == "current static NIFTY_100 list (or subset)"
    assert result["universe_metadata"]["historical_constituent_membership_available"] is False
    assert "survivorship bias" in result["universe_metadata"]["survivorship_bias_warning"]