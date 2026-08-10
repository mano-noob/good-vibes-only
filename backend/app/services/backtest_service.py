from app.services.market_data import MarketDataService
from app.indicators.technical_indicators import TechnicalIndicators
from app.strategies.breakout_strategy import BreakoutStrategy

import pandas as pd

nifty_df = MarketDataService.get_stock_data(
    symbol="^NSEI",
    period="5y"
)

nifty_df["EMA200"] = (
    nifty_df["Close"]
    .ewm(span=200, adjust=False)
    .mean()
)

class BacktestService:

    @staticmethod
    def run_backtest(
        symbol: str,
        stop_atr: int = 2,
        target_atr: int = 4,
        trail_atr=2.5,
        max_hold_days=40
    ):

        df = MarketDataService.get_stock_data(
            symbol=symbol,
            period="5y"
        )

        

        date_col = df.columns[0]

        df["EMA20"] = TechnicalIndicators.calculate_ema(df)
        df["RSI"] = TechnicalIndicators.calculate_rsi(df)
        df["ATR"] = TechnicalIndicators.calculate_atr(df)

        df["EMA50"] = (
            TechnicalIndicators
            .calculate_ema50(df)
        )

        df["EMA200"] = (
            TechnicalIndicators
            .calculate_ema200(df)
        )

        
        trades = []
        trade_log = []

        i = 200

        

        while i < len(df) - max_hold_days:

            sample = df.iloc[: i + 1]

            nifty_close = nifty_df.iloc[i]["Close"]

            nifty_ema200 = nifty_df.iloc[i]["EMA200"]

            if nifty_close < nifty_ema200:

                i += 1
                continue

            signal = BreakoutStrategy.generate_signal(sample)

            if signal["signal"] != "BUY":

                i += 1
                continue

            atr = df.iloc[i]["ATR"]
            entry_atr = atr

            if pd.isna(atr):

                i += 1
                continue

            entry_index = i + 1

            entry_price = df.iloc[entry_index]["Open"]

            active_stop = (
                entry_price -
                (stop_atr * atr)
            )

            highest_close = entry_price

            

            target_price = (
                entry_price +
                (target_atr * atr)
            )

            exit_price = None

            actual_exit_index = min(
                i + max_hold_days,
                len(df) - 1
            )

            for j in range(
                entry_index + 1,
                min(i + max_hold_days + 1, len(df))
            ):

                highest_close = max(
                    highest_close,
                    df.iloc[j]["Close"]
                )

                breakeven_trigger = (
                    entry_price
                    +
                    (2 * entry_atr)
                )

                if highest_close >= breakeven_trigger:

                    active_stop = max(

                        active_stop,

                        entry_price

                    )
                
                candle_high = df.iloc[j]["High"]

                candle_low = df.iloc[j]["Low"]

                if candle_high >= target_price:

                    exit_price = target_price

                    actual_exit_index = j

                    break

                if candle_low <= active_stop:
                    exit_price = active_stop
                    actual_exit_index = j
                    break

                
                current_atr = df.iloc[j]["ATR"]

                trail_stop = (
                    highest_close -
                    (trail_atr * current_atr)
                )

                active_stop = max(
                    active_stop,
                    trail_stop
                )

            if exit_price is None:

                exit_price = df.iloc[
                    actual_exit_index
                ]["Close"]

            pct_return = (
                (exit_price - entry_price)
                / entry_price
            ) * 100

            trades.append(pct_return)

            trade_log.append(
                {
                    "entry_date": str(
                        df.iloc[entry_index][date_col]
                    ),
                    "exit_date": str(
                        df.iloc[actual_exit_index][date_col]
                    ),
                    "entry_price": round(
                        entry_price,
                        2
                    ),
                    "exit_price": round(
                        exit_price,
                        2
                    ),
                    "return_pct": round(
                        pct_return,
                        2
                    )
                }
            )

            i = actual_exit_index + 1

       

        wins = len(
            [x for x in trades if x > 0]
        )

        losses = len(
            [x for x in trades if x <= 0]
        )

        winning_trades = [
            x for x in trades if x > 0
        ]

        losing_trades = [
            x for x in trades if x <= 0
        ]

        average_win = (
            round(
                sum(winning_trades)
                / len(winning_trades),
                2
            )
            if winning_trades
            else 0
        )

        average_loss = (
            round(
                abs(sum(losing_trades))
                / len(losing_trades),
                2
            )
            if losing_trades
            else 0
        )

        reward_risk_ratio = (
            round(
                average_win
                / average_loss,
                2
            )
            if average_loss > 0
            else None
        )

        expectancy = round(

            (
                (wins / len(trades))
                * average_win
            )
            -
            (
                (losses / len(trades))
                * average_loss
            ),

            2
        )

        gross_profit = sum(
            [x for x in trades if x > 0]
        )

        gross_loss = abs(
            sum(
                [x for x in trades if x < 0]
            )
        )

        profit_factor = (
            round(
                gross_profit / gross_loss,
                2
            )
            if gross_loss > 0
            else None
        )

        total_return = round(
            sum(trades),
            2
        )

        avg_return = round(
            sum(trades) / len(trades),
            2
        )

        return BacktestService.calculate_statistics(
            symbol,
            trades,
            trade_log
        )

    @staticmethod
    def calculate_statistics(symbol, trades, trade_log):

        if not trades:

            return {
                "symbol": symbol,
                "trades": 0,
                "gross_profit": 0,
                "gross_loss": 0,
                "profit_factor": None,
                "average_return": 0,
                "total_return": 0,
            }