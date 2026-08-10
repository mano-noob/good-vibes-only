import yfinance as yf
import pandas as pd
from functools import lru_cache


class MarketDataService:

    @staticmethod
    @lru_cache(maxsize=256)
    def get_stock_data(
        symbol: str,
        period: str = "2y",
        interval: str = "1d"
    ) -> pd.DataFrame:

        df = yf.download(
            symbol,
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False
        )

        if df.empty:
            raise ValueError(f"No data found for {symbol}")

        # Flatten multi-index columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df.reset_index(inplace=True)

        # Remove rows with NaN close prices
        df = df.dropna(subset=["Close"])

        return df