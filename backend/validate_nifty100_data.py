import time
from pathlib import Path

import pandas as pd

from app.core.watchlist import NIFTY_100
from app.services.market_data import MarketDataService


PERIOD = "5y"
OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / "nifty100_data_validation.csv"

results = []

symbols = list(NIFTY_100)

print("=" * 65)
print("NIFTY 100 HISTORICAL DATA VALIDATION")
print("=" * 65)
print(f"Total symbols: {len(symbols)}")
print(f"Requested history: {PERIOD}")
print()

for index, symbol in enumerate(symbols, start=1):

    print(f"[{index}/{len(symbols)}] Checking {symbol}...", end=" ")

    try:
        df = MarketDataService.get_stock_data(
            symbol=symbol,
            period=PERIOD
        )

        first_date = pd.to_datetime(df["Date"].min())
        last_date = pd.to_datetime(df["Date"].max())

        history_years = (
            (last_date - first_date).days / 365.25
        )

        valid = (
            not df.empty
            and df["Date"].is_monotonic_increasing
            and df["Date"].duplicated().sum() == 0
            and df.isna().sum().sum() == 0
        )

        status = "SUCCESS" if valid else "INVALID"

        results.append({
            "symbol": symbol,
            "status": status,
            "rows": len(df),
            "first_date": first_date.date(),
            "last_date": last_date.date(),
            "history_years": round(history_years, 2),
            "duplicates": int(df["Date"].duplicated().sum()),
            "missing_values": int(df.isna().sum().sum()),
            "chronological": bool(
                df["Date"].is_monotonic_increasing
            ),
            "error": None
        })

        print(
            f"{status} | {len(df)} rows | "
            f"{history_years:.2f} years"
        )

    except Exception as exc:

        results.append({
            "symbol": symbol,
            "status": "FAILED",
            "rows": 0,
            "first_date": None,
            "last_date": None,
            "history_years": 0,
            "duplicates": None,
            "missing_values": None,
            "chronological": False,
            "error": str(exc)[:250]
        })

        print(f"FAILED | {str(exc)[:150]}")

    # Small delay to reduce the risk of Yahoo Finance rate limiting.
    time.sleep(0.5)


# Generate report.
report = pd.DataFrame(results)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
report.to_csv(OUTPUT_FILE, index=False)

# Summary.
successful = int((report["status"] == "SUCCESS").sum())
failed = int((report["status"] == "FAILED").sum())
invalid = int((report["status"] == "INVALID").sum())

short_history = int(
    (
        (report["status"] == "SUCCESS")
        & (report["history_years"] < 4.5)
    ).sum()
)

print("\n" + "=" * 65)
print("VALIDATION SUMMARY")
print("=" * 65)

print(f"Universe size:       {len(symbols)}")
print(f"Unique symbols:      {len(set(symbols))}")
print(f"Successful:          {successful}")
print(f"Failed downloads:    {failed}")
print(f"Invalid datasets:    {invalid}")
print(f"Short history (<4.5 years): {short_history}")

print(f"\nReport saved to: {OUTPUT_FILE.resolve()}")

if successful == len(symbols):
    print("\nAll symbols returned valid datasets.")
else:
    print("\nSome symbols require investigation.")