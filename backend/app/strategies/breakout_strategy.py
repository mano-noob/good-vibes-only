import pandas as pd

from app.core.config_service import ConfigService


class BreakoutStrategy:

    @staticmethod
    def _value(key, default):
        return ConfigService.get(key, default)

    @staticmethod
    def generate_signal(df):

        if len(df) < 200:

            return {
                "signal": "NO SIGNAL",
                "reason": "Insufficient data"
            }

        latest = df.iloc[-1]

        breakout_lookback = BreakoutStrategy._value("breakout_lookback", 55)
        volume_lookback = BreakoutStrategy._value("volume_lookback", 20)
        consolidation_lookback = BreakoutStrategy._value("consolidation_lookback", 10)
        consolidation_range = BreakoutStrategy._value("consolidation_range", 0.08)
        volume_multiplier = BreakoutStrategy._value("volume_multiplier", 1.5)
        rsi_threshold = BreakoutStrategy._value("rsi_buy_threshold", 55)

        previous_55_high = (
            df["High"]
            .rolling(window=breakout_lookback)
            .max()
            .iloc[-2]
        )

        avg_volume = (
            df["Volume"]
            .rolling(window=volume_lookback)
            .mean()
            .iloc[-1]
        )

        last_10_high = (
            df["High"]
            .iloc[
                -(consolidation_lookback + 1):-1
            ]
            .max()
        )

        last_10_low = (
            df["Low"]
            .iloc[
                -(consolidation_lookback + 1):-1
            ]
            .min()
        )

        consolidation = bool(

            (
                last_10_high
                -
                last_10_low
            )

            /

            latest["Close"]

            <

            consolidation_range

        )

        breakout = bool(
            latest["Close"]
            > previous_55_high
        )

        candle_strength = bool(

            (

                latest["Close"]

                -

                latest["Low"]

            )

            /

            (

                latest["High"]

                -

                latest["Low"]

                +

                0.0001

            )

            >

            0.75

        )

        high_volume = bool(
            latest["Volume"]
            > avg_volume * volume_multiplier
        )

        rsi_condition = bool(
            latest["RSI"] > rsi_threshold
        )

        

        trend_condition = bool(

            latest["EMA50"]

            >

            latest["EMA200"]

        )

        
        if (

            breakout

            and

            high_volume

            and

            rsi_condition

            and

            trend_condition

            and consolidation

                                 
            
            
        ):

            return {

                "signal": "BUY",

                "reason":
                    "Breakout with volume and RSI confirmation",

                "diagnostics": {

                    "breakout": breakout,

                    "volume_confirmation": high_volume,

                    "rsi_confirmation": rsi_condition,

                    "trend_confirmation": trend_condition,
                    "consolidation": consolidation

                    

                }
            }

        return {

            "signal": "NO SIGNAL",

            "reason":
                "Conditions not met",

            "diagnostics": {

                "breakout": breakout,

                "volume_confirmation": high_volume,

                "rsi_confirmation": rsi_condition,
                "trend_confirmation": trend_condition,

                "consolidation": consolidation

            }
        }
    
    