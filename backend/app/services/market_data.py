
"""Cached market-data access for validated historical OHLCV price data."""

from functools import lru_cache

import numpy as np
import pandas as pd
import yfinance as yf


class MarketDataService:
    """Download, validate and normalize historical OHLCV data."""

    DEFAULT_PERIOD = "2y"
    DEFAULT_INTERVAL = "1d"

    REQUIRED_COLUMNS = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]

    @staticmethod
    @lru_cache(maxsize=256)
    def get_stock_data(
        symbol: str,
        period: str = DEFAULT_PERIOD,
        interval: str = DEFAULT_INTERVAL,
    ) -> pd.DataFrame:
        """
        Download and return clean historical OHLCV data.

        Processing:
        - Downloads adjusted historical prices.
        - Normalizes Yahoo Finance column formats.
        - Standardizes the date column.
        - Converts OHLCV values to numeric.
        - Removes invalid dates and duplicate sessions.
        - Sorts data chronologically.
        - Removes invalid price and volume observations.
        - Validates OHLC price consistency.

        Returns:
            DataFrame containing Date, Open, High, Low, Close, Volume.

        Raises:
            ValueError: If data is unavailable or invalid.
        """

        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("A valid stock symbol is required")

        df = yf.download(
            symbol.strip(),
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False,
            threads=False,
        )

        if df is None or df.empty:
            raise ValueError(f"No data found for {symbol}")

        df = df.copy()

        # Normalize Yahoo Finance MultiIndex columns.
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [
                col[0] if isinstance(col, tuple) else col
                for col in df.columns
            ]

        # Remove accidental duplicate column names.
        df = df.loc[:, ~pd.Index(df.columns).duplicated(keep="first")]

        # Standardize the date column.
        df = df.reset_index()

        if "Date" not in df.columns:
            if "Datetime" in df.columns:
                df = df.rename(columns={"Datetime": "Date"})
            else:
                raise ValueError(
                    f"Historical data for {symbol} has no Date column"
                )

        # Retain only the required market-data columns.
        missing_columns = [
            column
            for column in MarketDataService.REQUIRED_COLUMNS
            if column not in df.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Historical data for {symbol} is missing columns: "
                f"{missing_columns}"
            )

        df = df[["Date"] + MarketDataService.REQUIRED_COLUMNS].copy()

        # Normalize dates.
        df["Date"] = pd.to_datetime(
            df["Date"],
            errors="coerce",
            utc=True,
        )

        df["Date"] = df["Date"].dt.tz_convert(None)

        # Remove invalid dates.
        df = df.dropna(subset=["Date"])

        if df.empty:
            raise ValueError(
                f"Historical data for {symbol} contains no valid dates"
            )

        # Convert market values to numeric.
        for column in MarketDataService.REQUIRED_COLUMNS:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

        # Replace infinite values with NaN.
        df[MarketDataService.REQUIRED_COLUMNS] = (
            df[MarketDataService.REQUIRED_COLUMNS]
            .replace([np.inf, -np.inf], np.nan)
        )

        # Remove rows with incomplete OHLCV observations.
        df = df.dropna(
            subset=MarketDataService.REQUIRED_COLUMNS
        )

        # Remove zero or negative prices.
        price_columns = ["Open", "High", "Low", "Close"]

        valid_prices = (
            df[price_columns] > 0
        ).all(axis=1)

        # Volume must be non-negative.
        valid_volume = df["Volume"] >= 0

        # Validate candle consistency.
        valid_high = (
            df["High"] >= df[["Open", "Close", "Low"]].max(axis=1)
        )

        valid_low = (
            df["Low"] <= df[["Open", "Close", "High"]].min(axis=1)
        )

        df = df[
            valid_prices
            & valid_volume
            & valid_high
            & valid_low
        ]

        if df.empty:
            raise ValueError(
                f"Historical data for {symbol} contains no valid OHLCV rows"
            )

        # Sort chronologically.
        df = df.sort_values(
            "Date",
            ascending=True,
        )

        # Remove duplicate trading sessions.
        df = df.drop_duplicates(
            subset=["Date"],
            keep="last",
        )

        # Return a clean, sequential index.
        df = df.reset_index(drop=True)

        if len(df) < 1:
            raise ValueError(
                f"Insufficient valid historical data for {symbol}"
            )

        return df