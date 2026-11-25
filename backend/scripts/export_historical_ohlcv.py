import sys
from pathlib import Path

import pandas as pd

# Add backend directory to Python path
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.core.watchlist import NIFTY_100
from app.services.market_data import MarketDataService


# Configuration
START_DATE = "2024-01-01"
END_DATE = "2026-11-17"

OUTPUT_DIR = BACKEND_DIR / "data"
OUTPUT_FILE = OUTPUT_DIR / "historical_ohlcv_2025_2026.csv"

BENCHMARK = "^NSEI"

REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


def prepare_data(df, symbol):

    if df is None or df.empty:
        raise ValueError(f"No data returned for {symbol}")

    df = df.copy()

    # Handle MultiIndex columns if returned by Yahoo Finance
    if isinstance(df.columns, pd.MultiIndex):
        for level in range(df.columns.nlevels):
            if symbol in df.columns.get_level_values(level):
                df = df.xs(symbol, axis=1, level=level)
                break

    # Extract date
    if "Date" in df.columns:
        dates = pd.to_datetime(df["Date"], errors="coerce")
    elif "Datetime" in df.columns:
        dates = pd.to_datetime(df["Datetime"], errors="coerce")
    else:
        dates = pd.to_datetime(df.index, errors="coerce")

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing:
        raise ValueError(f"{symbol}: Missing columns {missing}")

    result = pd.DataFrame({
        "date": dates,
        "symbol": symbol,
        "open": pd.to_numeric(df["Open"], errors="coerce").values,
        "high": pd.to_numeric(df["High"], errors="coerce").values,
        "low": pd.to_numeric(df["Low"], errors="coerce").values,
        "close": pd.to_numeric(df["Close"], errors="coerce").values,
        "volume": pd.to_numeric(df["Volume"], errors="coerce").values,
    })

    result["date"] = pd.to_datetime(result["date"]).dt.normalize()

    # Retain warm-up history for technical indicators
    result = result[
        (result["date"] >= START_DATE) &
        (result["date"] <= END_DATE)
    ]

    result = result.dropna()

    if result.empty:
        raise ValueError(f"{symbol}: No valid records in requested date range")

    result = result.drop_duplicates(subset=["date"], keep="last")
    result = result.sort_values("date")

    return result


def main():

    symbols = list(dict.fromkeys(NIFTY_100))

    print(f"Starting OHLCV export")
    print(f"NIFTY 100 symbols: {len(symbols)}")

    if len(symbols) != 100:
        raise RuntimeError(
            f"Expected 100 unique NIFTY 100 symbols, found {len(symbols)}. "
            "Check watchlist.py before exporting."
        )

    all_data = []
    errors = []

    # Download individual stocks
    for i, symbol in enumerate(symbols, 1):

        try:
            print(f"[{i}/100] Downloading {symbol}...")

            df = MarketDataService.get_stock_data(
                symbol=symbol,
                period="5y"
            )

            prepared = prepare_data(df, symbol)
            all_data.append(prepared)

            print(
                f"    Records: {len(prepared)} | "
                f"{prepared['date'].min().date()} to "
                f"{prepared['date'].max().date()}"
            )

        except Exception as exc:
            errors.append({
                "symbol": symbol,
                "error": str(exc)
            })
            print(f"    FAILED: {exc}")

    # Download NIFTY 50 benchmark
    print("\nDownloading NIFTY 50 benchmark...")

    try:
        benchmark_df = MarketDataService.get_stock_data(
            symbol=BENCHMARK,
            period="5y"
        )

        benchmark_data = prepare_data(benchmark_df, BENCHMARK)
        all_data.append(benchmark_data)

        print(f"Benchmark records: {len(benchmark_data)}")

    except Exception as exc:
        errors.append({
            "symbol": BENCHMARK,
            "error": str(exc)
        })

    # Do not export an incomplete dataset
    if errors:
        print("\nEXPORT ABORTED")
        print(f"Failed downloads: {len(errors)}")

        for error in errors:
            print(error)

        raise RuntimeError(
            "Some downloads failed. No incomplete CSV was exported."
        )

    # Combine all data
    final_df = pd.concat(all_data, ignore_index=True)

    final_df = final_df.sort_values(
        ["symbol", "date"]
    ).reset_index(drop=True)

    # Final validation
    if final_df.isnull().any().any():
        raise RuntimeError("Final dataset contains missing values")

    expected_symbols = set(symbols + [BENCHMARK])
    actual_symbols = set(final_df["symbol"].unique())

    if expected_symbols != actual_symbols:
        raise RuntimeError("Final dataset is missing one or more symbols")

    # Export
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    final_df.to_csv(OUTPUT_FILE, index=False)

    print("\nEXPORT COMPLETED")
    print(f"Total records: {len(final_df):,}")
    print(f"Total symbols: {final_df['symbol'].nunique()}")
    print(f"Date range: {final_df['date'].min().date()} to "
          f"{final_df['date'].max().date()}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()