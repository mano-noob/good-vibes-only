import pandas as pd

from app.core.config_service import ConfigService


class TechnicalIndicators:

    @staticmethod
    def calculate_ema(
        df: pd.DataFrame,
        period: int = None
    ) -> pd.Series:

        if period is None:
            period = ConfigService.get("ema_fast", 20)

        return df["Close"].ewm(
            span=period,
            adjust=False
        ).mean()

    @staticmethod
    def calculate_rsi(
        df: pd.DataFrame,
        period: int = 14
    ) -> pd.Series:

        delta = df["Close"].diff()

        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss

        rsi = 100 - (100 / (1 + rs))

        return rsi
    
    @staticmethod
    def calculate_atr(df, period=14):

        high_low = df["High"] - df["Low"]

        high_close = (
            df["High"] -
            df["Close"].shift()
        ).abs()

        low_close = (
            df["Low"] -
            df["Close"].shift()
        ).abs()

        tr = pd.concat(
            [
                high_low,
                high_close,
                low_close
            ],
            axis=1
        ).max(axis=1)

        atr = tr.rolling(period).mean()

        return atr
    
    @staticmethod
    def calculate_ema50(df):

        return (
            df["Close"]
            .ewm(span=ConfigService.get("ema_medium", 50), adjust=False)
            .mean()
        )


    @staticmethod
    def calculate_ema200(df):

        return (
            df["Close"]
            .ewm(span=ConfigService.get("ema_slow", 200), adjust=False)
            .mean()
        )
    
    @staticmethod
    def calculate_adx(df, period=14):

        high = df["High"]
        low = df["Low"]
        close = df["Close"]

        plus_dm = high.diff()
        minus_dm = -low.diff()

        plus_dm = plus_dm.where(
            (plus_dm > minus_dm) & (plus_dm > 0),
            0
        )

        minus_dm = minus_dm.where(
            (minus_dm > plus_dm) & (minus_dm > 0),
            0
        )

        tr1 = high - low

        tr2 = (
            high - close.shift()
        ).abs()

        tr3 = (
            low - close.shift()
        ).abs()

        tr = pd.concat(
            [tr1, tr2, tr3],
            axis=1
        ).max(axis=1)

        atr = tr.rolling(period).mean()

        plus_di = (
            100 *
            (
                plus_dm.rolling(period).mean()
                / atr
            )
        )

        minus_di = (
            100 *
            (
                minus_dm.rolling(period).mean()
                / atr
            )
        )

        dx = (
            (
                (plus_di - minus_di).abs()
                /
                (plus_di + minus_di)
            )
            * 100
        )

        adx = dx.rolling(period).mean()

        return adx