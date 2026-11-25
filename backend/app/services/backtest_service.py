import json
import re
from datetime import datetime, timezone
from pathlib import Path

from app.services.market_data import MarketDataService
from app.indicators.technical_indicators import TechnicalIndicators
from app.strategies.breakout_strategy import BreakoutStrategy
from app.core.config_service import ConfigService
from app.services.market_regime_service import MarketRegimeService
from runtime_paths import DATA_DIR

import pandas as pd

class BacktestService:

    DEFAULT_BROKERAGE_PCT = 0.03
    DEFAULT_TRANSACTION_COST_PCT = 0.10
    DEFAULT_SLIPPAGE_BPS = 5.0
    TRADE_LOG_DIR = DATA_DIR / "backtest_logs"

    @staticmethod
    def _holding_days(entry_date, exit_date):
        try:
            entry = pd.to_datetime(entry_date, errors="raise").normalize()
            exit = pd.to_datetime(exit_date, errors="raise").normalize()
        except (TypeError, ValueError):
            return None
        return max(0, (exit - entry).days)

    @staticmethod
    def persist_trade_log(symbol, trade_log, assumptions=None):
        safe_symbol = re.sub(r"[^A-Za-z0-9._-]+", "_", str(symbol)).strip("._-")
        if not safe_symbol:
            safe_symbol = "symbol"

        BacktestService.TRADE_LOG_DIR.mkdir(parents=True, exist_ok=True)
        generated_at = datetime.now(timezone.utc)
        filename_timestamp = generated_at.strftime("%Y%m%dT%H%M%S.%fZ")
        log_path = BacktestService.TRADE_LOG_DIR / f"{safe_symbol}_{filename_timestamp}.json"

        normalized_trades = []
        for trade in trade_log:
            record = dict(trade)
            record.setdefault("symbol", str(symbol))
            record["holding_days"] = BacktestService._holding_days(
                record.get("entry_date"),
                record.get("exit_date"),
            )
            normalized_trades.append(record)

        payload = {
            "symbol": str(symbol),
            "generated_at": generated_at.isoformat(),
            "cost_assumptions": assumptions or BacktestService.cost_assumptions(),
            "trade_count": len(normalized_trades),
            "trades": normalized_trades,
        }
        temporary_path = log_path.with_suffix(".tmp")
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2, default=str)
        temporary_path.replace(log_path)
        return log_path

    @staticmethod
    def load_trade_log(log_path):
        with Path(log_path).open("r", encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def cost_assumptions():
        """Rates are per side: brokerage 0.03%, other charges 0.10%, slippage 5 bps.

        Other transaction charges are modeled as one combined percentage. These
        illustrative defaults are not a broker-specific fee or tax estimate.
        """
        return {
            "brokerage_pct": float(ConfigService.get(
                "backtest_brokerage_pct",
                BacktestService.DEFAULT_BROKERAGE_PCT,
            )),
            "transaction_cost_pct": float(ConfigService.get(
                "backtest_transaction_cost_pct",
                BacktestService.DEFAULT_TRANSACTION_COST_PCT,
            )),
            "slippage_bps": float(ConfigService.get(
                "backtest_slippage_bps",
                BacktestService.DEFAULT_SLIPPAGE_BPS,
            )),
        }

    @staticmethod
    def calculate_execution_costs(entry_price, exit_price, assumptions=None):
        assumptions = assumptions or BacktestService.cost_assumptions()
        entry_reference = float(entry_price)
        exit_reference = float(exit_price)
        brokerage_rate = float(assumptions["brokerage_pct"]) / 100.0
        transaction_rate = float(assumptions["transaction_cost_pct"]) / 100.0
        slippage_rate = float(assumptions["slippage_bps"]) / 10000.0

        entry_fill = entry_reference * (1 + slippage_rate)
        exit_fill = exit_reference * (1 - slippage_rate)
        brokerage_cost = (entry_fill + exit_fill) * brokerage_rate
        transaction_cost = (entry_fill + exit_fill) * transaction_rate
        entry_outlay = entry_fill * (1 + brokerage_rate + transaction_rate)
        slippage_cost = (entry_fill - entry_reference) + (exit_reference - exit_fill)
        gross_profit = exit_reference - entry_reference
        net_profit = exit_fill - entry_fill - brokerage_cost - transaction_cost

        return {
            "entry_fill_price": entry_fill,
            "exit_fill_price": exit_fill,
            "brokerage_cost": brokerage_cost,
            "transaction_cost": transaction_cost,
            "slippage_cost": slippage_cost,
            "gross_profit_per_share": gross_profit,
            "net_profit_per_share": net_profit,
            "gross_return_pct": (gross_profit / entry_reference * 100) if entry_reference else 0.0,
            "net_return_pct": (net_profit / entry_outlay * 100) if entry_outlay else 0.0,
        }

    @staticmethod
    def _market_regimes_for_dates(market_df, stock_dates):
        if market_df is None or market_df.empty or len(market_df.columns) == 0:
            raise ValueError("Historical NIFTY data is unavailable")

        date_column = market_df.columns[0]
        market_dates = pd.to_datetime(market_df[date_column], errors="coerce").dt.normalize()
        ema50 = TechnicalIndicators.calculate_ema50(market_df)
        ema200 = TechnicalIndicators.calculate_ema200(market_df)
        regimes = [
            MarketRegimeService.is_bullish_ema(fast, slow)
            for fast, slow in zip(ema50, ema200)
        ]
        regime_series = pd.Series(regimes, index=market_dates)
        regime_series = regime_series[~regime_series.index.isna()]
        regime_series = regime_series[~regime_series.index.duplicated(keep="last")]

        if regime_series.empty or regime_series.notna().sum() == 0:
            raise ValueError("Historical NIFTY EMA50/EMA200 regime data is unavailable")

        aligned_dates = pd.DatetimeIndex(
            pd.to_datetime(stock_dates, errors="coerce")
        ).normalize()
        aligned = regime_series.reindex(aligned_dates)
        if aligned.notna().sum() == 0:
            raise ValueError("Historical NIFTY regime does not overlap the stock data")
        return aligned.reset_index(drop=True)

    @staticmethod
    def run(symbol: str, stop_atr: int = 2, target_atr: int = 4, trail_atr=2.5, max_hold_days=40):

        return BacktestService.run_backtest(
            symbol=symbol,
            stop_atr=stop_atr,
            target_atr=target_atr,
            trail_atr=trail_atr,
            max_hold_days=max_hold_days,
        )

    @staticmethod
    def run_portfolio(symbols, stop_atr: int = 2, target_atr: int = 4, trail_atr=2.5, max_hold_days=40):

        results = []
        for symbol in symbols:
            results.append(
                BacktestService.run(
                    symbol=symbol,
                    stop_atr=stop_atr,
                    target_atr=target_atr,
                    trail_atr=trail_atr,
                    max_hold_days=max_hold_days,
                )
            )

        return {
            "results": results,
            "symbols": list(symbols),
        }

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
        ).copy()

        nifty_df = MarketDataService.get_stock_data(
            symbol="^NSEI",
            period="5y",
        ).copy()

        date_col = df.columns[0]
        historical_regimes = BacktestService._market_regimes_for_dates(
            nifty_df,
            df[date_col],
        )

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
        persisted_trade_log = []
        assumptions = BacktestService.cost_assumptions()

        i = 200

        

        while i < len(df) - max_hold_days:

            sample = df.iloc[: i + 1]

            market_regime = historical_regimes.iloc[i]
            if pd.isna(market_regime) or not bool(market_regime):

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

            reference_entry_price = float(df.iloc[entry_index]["Open"])
            entry_price = reference_entry_price * (
                1 + assumptions["slippage_bps"] / 10000.0
            )

            active_stop = (
                entry_price -
                (stop_atr * atr)
            )
            active_stop_reason = "stop-loss"

            highest_close = entry_price

            

            target_price = (
                entry_price +
                (target_atr * atr)
            )

            exit_price = None
            exit_reason = "other"

            actual_exit_index = min(
                i + max_hold_days,
                len(df) - 1
            )

            for j in range(
                entry_index,
                min(i + max_hold_days + 1, len(df))
            ):
                candle_high = df.iloc[j]["High"]
                candle_low = df.iloc[j]["Low"]

                if candle_high >= target_price:

                    exit_price = target_price
                    exit_reason = "target"

                    actual_exit_index = j

                    break

                if candle_low <= active_stop:
                    opening_price = float(df.iloc[j]["Open"])
                    exit_price = min(active_stop, opening_price)
                    exit_reason = active_stop_reason
                    actual_exit_index = j
                    break

                # Close-confirmed stop changes apply from the next candle.
                highest_close = max(highest_close, df.iloc[j]["Close"])
                breakeven_trigger = entry_price + (2 * entry_atr)
                if highest_close >= breakeven_trigger:
                    if entry_price > active_stop:
                        active_stop = entry_price
                        active_stop_reason = "trailing stop"

                current_atr = df.iloc[j]["ATR"]

                trail_stop = (
                    highest_close -
                    (trail_atr * current_atr)
                )

                if trail_stop > active_stop:
                    active_stop = trail_stop
                    active_stop_reason = "trailing stop"

            if exit_price is None:

                exit_price = df.iloc[
                    actual_exit_index
                ]["Close"]

            execution = BacktestService.calculate_execution_costs(
                reference_entry_price,
                float(exit_price),
                assumptions,
            )
            pct_return = execution["net_return_pct"]
            trades.append(pct_return)

            trade_record = {
                    "entry_date": str(
                        df.iloc[entry_index][date_col]
                    ),
                    "exit_date": str(
                        df.iloc[actual_exit_index][date_col]
                    ),
                    "entry_price": round(execution["entry_fill_price"], 2),
                    "exit_price": round(
                        execution["exit_fill_price"],
                        2
                    ),
                    "reference_entry_price": round(reference_entry_price, 2),
                    "reference_exit_price": round(float(exit_price), 2),
                    "gross_return_pct": round(execution["gross_return_pct"], 4),
                    "return_pct": round(
                        pct_return,
                        4
                    ),
                    "brokerage_cost_per_share": round(execution["brokerage_cost"], 4),
                    "transaction_cost_per_share": round(execution["transaction_cost"], 4),
                    "slippage_cost_per_share": round(execution["slippage_cost"], 4),
                    "cost_assumptions": assumptions,
            }
            trade_log.append(trade_record)
            entry_regime = historical_regimes.iloc[entry_index]
            persisted_trade_log.append({
                **trade_record,
                "symbol": symbol,
                "entry_market_regime": (
                    "Bullish"
                    if pd.notna(entry_regime) and bool(entry_regime)
                    else "Bearish"
                    if pd.notna(entry_regime)
                    else "Unknown"
                ),
                "holding_days": BacktestService._holding_days(
                    trade_record["entry_date"],
                    trade_record["exit_date"],
                ),
                "exit_reason": exit_reason,
            })

            i = actual_exit_index + 1

        result = BacktestService.calculate_statistics(
            symbol,
            trades,
            trade_log
        )
        BacktestService.persist_trade_log(symbol, persisted_trade_log, assumptions)
        return result

    @staticmethod
    def calculate_statistics(symbol, trades, trade_log):
        net_returns = [float(value) for value in trades]
        gross_returns = [
            float(item.get("gross_return_pct", item.get("return_pct", 0)))
            for item in trade_log
        ]
        if not gross_returns:
            gross_returns = net_returns

        winning_returns = [value for value in net_returns if value > 0]
        losing_returns = [value for value in net_returns if value < 0]
        breakeven_trades = sum(value == 0 for value in net_returns)
        wins = len(winning_returns)
        losses = len(losing_returns)
        trade_count = len(net_returns)
        gross_profit = sum(value for value in gross_returns if value > 0)
        gross_loss = abs(sum(value for value in gross_returns if value < 0))
        net_profit = sum(winning_returns)
        net_loss = abs(sum(value for value in losing_returns if value < 0))
        average_return = sum(net_returns) / trade_count if trade_count else 0.0
        average_win = sum(winning_returns) / wins if wins else 0.0
        average_loss = abs(sum(losing_returns)) / losses if losses else 0.0
        win_rate = wins / trade_count * 100 if trade_count else 0.0
        profit_factor = net_profit / net_loss if net_loss else None
        reward_risk_ratio = average_win / average_loss if average_loss else None

        return {
            "symbol": symbol,
            "trades": trade_count,
            "wins": wins,
            "losses": losses,
            "breakeven_trades": breakeven_trades,
            "win_rate": round(win_rate, 2),
            "gross_profit": round(gross_profit, 4),
            "gross_loss": round(gross_loss, 4),
            "net_profit": round(net_profit, 4),
            "net_loss": round(net_loss, 4),
            "profit_factor": round(profit_factor, 2) if profit_factor is not None else None,
            "average_return": round(average_return, 4),
            "average_win": round(average_win, 4),
            "average_loss": round(average_loss, 4),
            "reward_risk_ratio": round(reward_risk_ratio, 2) if reward_risk_ratio is not None else None,
            "expectancy": round(average_return, 4),
            "total_return": round(sum(net_returns), 4),
            "trade_log": trade_log,
        }