"""Cached market-data access for price history lookups."""

from functools import lru_cache

import pandas as pd
import yfinance as yf


class MarketDataService:
    """Download and normalize OHLCV history for symbols."""

    DEFAULT_PERIOD = "2y"
    DEFAULT_INTERVAL = "1d"

    @staticmethod
    @lru_cache(maxsize=256)
    def get_stock_data(
        symbol: str,
        period: str = DEFAULT_PERIOD,
        interval: str = DEFAULT_INTERVAL,
    ) -> pd.DataFrame:
        df = yf.download(
            symbol,
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False,
        )

        if df.empty:
            raise ValueError(f"No data found for {symbol}")

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()
        return df.dropna(subset=["Close"])