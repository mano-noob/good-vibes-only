"""
Standalone NIFTY 100 strategy experiment runner.

Run from the backend directory:
    python run_nifty100_experiment.py

This script downloads five years of daily data, runs the isolated
StrategyExperimentService experiment, and writes JSON/CSV outputs under
backend/data/nifty100_strategy_experiments/.

It does not modify live trading state or the existing application pipeline.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

# Ensure `app` imports work when this script is launched from another directory.
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config_service import ConfigService
from app.core.watchlist import NIFTY_100
from app.services.backtest_service import BacktestService
from app.services.market_data import MarketDataService
from app.services.strategy_experiment_service import StrategyExperimentService


PERIOD = "5y"
INTERVAL = "1d"
BENCHMARK_SYMBOL = "^NSEI"
OUTPUT_ROOT = BACKEND_DIR / "data" / "nifty100_strategy_experiments"


def json_default(value: Any) -> Any:
    """Convert common NumPy/Pandas values into JSON-safe values."""
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def download_data() -> tuple[dict[str, pd.DataFrame], pd.DataFrame, dict[str, Any]]:
    symbols = list(NIFTY_100)

    if len(symbols) != 100 or len(set(symbols)) != 100:
        raise RuntimeError(
            f"Expected 100 unique NIFTY_100 symbols; found {len(symbols)} "
            f"symbols and {len(set(symbols))} unique symbols."
        )

    stock_frames: dict[str, pd.DataFrame] = {}
    failures: list[dict[str, str]] = []
    coverage: dict[str, dict[str, Any]] = {}

    print(f"Downloading {PERIOD} of daily data for {len(symbols)} NIFTY 100 stocks...")

    for number, symbol in enumerate(symbols, start=1):
        try:
            frame = MarketDataService.get_stock_data(
                symbol=symbol,
                period=PERIOD,
                interval=INTERVAL,
            )
            if frame is None or frame.empty:
                raise ValueError("No rows returned")

            frame = frame.copy()
            date_col = frame.columns[0]
            dates = pd.to_datetime(frame[date_col], errors="coerce").dropna()

            if dates.empty:
                raise ValueError("No valid dates in downloaded data")

            stock_frames[symbol] = frame
            coverage[symbol] = {
                "rows": int(len(frame)),
                "first_date": dates.min().date().isoformat(),
                "last_date": dates.max().date().isoformat(),
                "years_approx": round(
                    (dates.max() - dates.min()).days / 365.25, 2
                ),
            }
            print(
                f"[{number:03d}/100] {symbol}: {len(frame)} rows "
                f"({coverage[symbol]['first_date']} to {coverage[symbol]['last_date']})"
            )
        except Exception as exc:
            failures.append({"symbol": symbol, "error": str(exc)})
            print(f"[{number:03d}/100] FAILED {symbol}: {exc}")

    print(f"\nDownloading benchmark {BENCHMARK_SYMBOL}...")
    benchmark = MarketDataService.get_stock_data(
        symbol=BENCHMARK_SYMBOL,
        period=PERIOD,
        interval=INTERVAL,
    )
    if benchmark is None or benchmark.empty:
        raise RuntimeError(f"No benchmark data returned for {BENCHMARK_SYMBOL}")

    benchmark_dates = pd.to_datetime(
        benchmark.iloc[:, 0], errors="coerce"
    ).dropna()

    if failures:
        failed_symbols = ", ".join(item["symbol"] for item in failures)
        raise RuntimeError(
            f"{len(failures)} NIFTY 100 downloads failed: {failed_symbols}. "
            "The experiment was not run because it must use the complete "
            "configured NIFTY 100 universe. Resolve the data issue and rerun."
        )

    if len(stock_frames) != 100:
        raise RuntimeError(
            f"Expected 100 downloaded stocks, received {len(stock_frames)}."
        )

    metadata = {
        "requested_period": PERIOD,
        "requested_interval": INTERVAL,
        "stock_count": len(stock_frames),
        "benchmark_symbol": BENCHMARK_SYMBOL,
        "benchmark_rows": int(len(benchmark)),
        "benchmark_first_date": benchmark_dates.min().date().isoformat(),
        "benchmark_last_date": benchmark_dates.max().date().isoformat(),
        "stock_coverage": coverage,
        "download_failures": failures,
    }
    return stock_frames, benchmark, metadata


def build_output_tables(result: dict[str, Any]) -> dict[str, pd.DataFrame]:
    test_results = result.get("test_results", {})
    summary_rows = []
    attribution_rows = []
    quarterly_rows = []

    for variant, metrics in test_results.items():
        if metrics is None:
            summary_rows.append({"variant": variant, "status": "No result"})
            continue

        summary_rows.append(
            {
                "variant": variant,
                "status": "completed",
                "trade_count": metrics.get("trade_count"),
                "win_rate_pct": metrics.get("win_rate_pct"),
                "net_expectancy": metrics.get("net_expectancy"),
                "profit_factor": metrics.get("profit_factor"),
                "net_return_pct": metrics.get("net_return_pct"),
                "maximum_drawdown_pct": metrics.get("maximum_drawdown_pct"),
                "average_exposure_pct": metrics.get("average_exposure_pct"),
                "maximum_exposure_pct": metrics.get("maximum_exposure_pct"),
                "average_cash_utilization_pct": metrics.get("average_cash_utilization_pct_of_starting_capital"),
                "maximum_cash_utilization_pct": metrics.get("maximum_cash_utilization_pct_of_starting_capital"),
                "ending_equity": metrics.get("ending_equity"),
                "max_concurrent_positions": metrics.get("max_concurrent_positions"),
            }
        )

        for symbol, values in metrics.get("per_stock_attribution", {}).items():
            attribution_rows.append(
                {"variant": variant, "symbol": symbol, **values}
            )

        for quarter in metrics.get("quarterly_summaries", []):
            quarterly_rows.append({"variant": variant, **quarter})

    return {
        "test_summary": pd.DataFrame(summary_rows),
        "per_stock_attribution": pd.DataFrame(attribution_rows),
        "quarterly_summary": pd.DataFrame(quarterly_rows),
    }


def main() -> None:
    started_at = datetime.now().astimezone()
    print("=" * 72)
    print("NIFTY 100 STRATEGY EXPERIMENT")
    print("=" * 72)
    print(f"Started: {started_at.isoformat()}")
    print(f"Universe: {len(NIFTY_100)} configured NIFTY 100 symbols")
    print(f"Data: {PERIOD}, {INTERVAL}")
    print(f"Starting capital: {ConfigService.get('capital', 100000)}")

    stock_data, benchmark_data, data_metadata = download_data()

    print("\nRunning train/test strategy experiment...")
    result = StrategyExperimentService.run_experiment(
        stock_data=stock_data,
        benchmark_data=benchmark_data,
    )

    finished_at = datetime.now().astimezone()
    result["run_metadata"] = {
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": round((finished_at - started_at).total_seconds(), 2),
        "data": data_metadata,
        "cost_assumptions": BacktestService.cost_assumptions(),
        "starting_capital": float(ConfigService.get("capital", 100000)),
        "note": (
            "Current static NIFTY 100 membership is used. This is an exploratory "
            "approximation and is subject to survivorship bias because historical "
            "index constituent membership is not available."
        ),
    }

    run_id = started_at.strftime("%Y%m%d_%H%M%S")
    output_dir = OUTPUT_ROOT / f"run_{run_id}"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "experiment_results.json"
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(
            result,
            handle,
            indent=2,
            ensure_ascii=False,
            default=json_default,
            allow_nan=False,
        )

    tables = build_output_tables(result)
    csv_paths = {}
    for name, table in tables.items():
        path = output_dir / f"{name}.csv"
        table.to_csv(path, index=False)
        csv_paths[name] = path

    print("\n" + "=" * 72)
    print("EXPERIMENT RESULTS")
    print("=" * 72)
    print(f"Training period: {result['periods']['training_start']} to "
          f"{result['periods']['training_end']}")
    print(f"Test period:     {result['periods']['test_start']} to "
          f"{result['periods']['test_end']}")
    print(f"Aligned sessions: {result['periods']['aligned_sessions']}")
    print(
        f"NIFTY 50 benchmark return: "
        f"{result['benchmark']['test_return_pct']:.2f}%"
    )

    summary = tables["test_summary"]
    if not summary.empty:
        display_columns = [
            column
            for column in (
                "variant",
                "status",
                "trade_count",
                "win_rate_pct",
                "net_return_pct",
                "maximum_drawdown_pct",
                "profit_factor",
                "net_expectancy",
                "ending_equity",
                "average_exposure_pct",
                "maximum_exposure_pct",
                "average_cash_utilization_pct_of_starting_capital",
                "maximum_cash_utilization_pct_of_starting_capital",
            )
            if column in summary.columns
        ]
        print("\nOut-of-sample comparison:")
        print(summary[display_columns].to_string(index=False))

    print("\nFixed variants:")
    print(json.dumps(result.get("variants", {}), indent=2))

    print(f"\nFull JSON: {json_path}")
    for name, path in csv_paths.items():
        print(f"{name}: {path}")
    print(f"\nCompleted in {result['run_metadata']['duration_seconds']} seconds.")


if __name__ == "__main__":
    main()
