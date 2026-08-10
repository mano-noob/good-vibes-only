import pandas as pd


class BreakoutStrategy:

    BREAKOUT_LOOKBACK = 55
    VOLUME_LOOKBACK = 20
    CONSOLIDATION_LOOKBACK = 10

    RSI_THRESHOLD = 55
    VOLUME_MULTIPLIER = 1.5
    CONSOLIDATION_RANGE = 0.08

    @staticmethod
    def generate_signal(df):

        if len(df) < 200:

            return {
                "signal": "NO SIGNAL",
                "reason": "Insufficient data"
            }

        latest = df.iloc[-1]

        previous_55_high = (
            df["High"]
            .rolling(window=BreakoutStrategy.BREAKOUT_LOOKBACK)
            .max()
            .iloc[-2]
        )

        avg_volume = (
            df["Volume"]
            .rolling(window=BreakoutStrategy.VOLUME_LOOKBACK)
            .mean()
            .iloc[-1]
        )

        
        last_10_high = (
            df["High"]
            .iloc[
                -(BreakoutStrategy.CONSOLIDATION_LOOKBACK + 1):-1
            ]
            .max()
        )

        last_10_low = (
            df["Low"]
            .iloc[
                -(BreakoutStrategy.CONSOLIDATION_LOOKBACK + 1):-1
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

            BreakoutStrategy.CONSOLIDATION_RANGE

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
            > avg_volume * BreakoutStrategy.VOLUME_MULTIPLIER
        )

        rsi_condition = bool(
            latest["RSI"] > BreakoutStrategy.RSI_THRESHOLD
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
    
    