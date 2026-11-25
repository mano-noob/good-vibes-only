from __future__ import annotations

import math
from typing import Any

import pandas as pd

from app.core.config_service import ConfigService
from app.core.watchlist import NIFTY_100
from app.indicators.technical_indicators import TechnicalIndicators
from app.services.backtest_service import BacktestService
from app.services.market_regime_service import MarketRegimeService
from app.services.risk_management_service import RiskManagementService
from app.strategies.breakout_strategy import BreakoutStrategy


class StrategyExperimentService:
    """Run isolated, prepared-data out-of-sample comparisons without live-state changes."""

    SPLIT_RATIO = 0.70
    STOP_ATR = 2.0
    TARGET_ATR = 4.0
    TRAIL_ATR = 2.5
    MAX_HOLD_DAYS = 40

    VARIANTS = {
        "baseline": {
            "name": "Baseline",
            "breakout_distance_pct": None,
            "relative_volume": None,
            "relative_strength_pct": None,
        },
        "breakout_1_5": {
            "name": "Breakout 1.5%",
            "breakout_distance_pct": 1.5,
            "relative_volume": None,
            "relative_strength_pct": None,
        },
        "breakout_2": {
            "name": "Breakout 2%",
            "breakout_distance_pct": 2.0,
            "relative_volume": None,
            "relative_strength_pct": None,
        },
        "breakout_volume": {
            "name": "Breakout + Volume",
            "breakout_distance_pct": 1.5,
            "relative_volume": 2.0,
            "relative_strength_pct": None,
        },
        "breakout_relative_strength": {
            "name": "Breakout + Relative Strength",
            "breakout_distance_pct": 1.5,
            "relative_volume": None,
            "relative_strength_pct": 5.0,
        },
        "combined": {
            "name": "Combined",
            "breakout_distance_pct": 1.5,
            "relative_volume": 2.0,
            "relative_strength_pct": 5.0,
        },
    }

    @staticmethod
    def align_prepared_data(
        stock_data: dict[str, pd.DataFrame],
        benchmark_data: pd.DataFrame,
    ) -> tuple[dict[str, pd.DataFrame], pd.DataFrame, pd.DatetimeIndex]:
        if not stock_data:
            raise ValueError("At least one prepared stock frame is required")
        if benchmark_data is None or benchmark_data.empty:
            raise ValueError("Prepared benchmark data is required")

        frames = {}
        date_sets = []
        for symbol in sorted(stock_data):
            frame = stock_data[symbol].copy()
            if frame.empty:
                raise ValueError(f"Prepared data is empty for {symbol}")
            date_column = frame.columns[0]
            frame["_experiment_date"] = pd.to_datetime(
                frame[date_column], errors="coerce"
            ).dt.normalize()
            frame = frame.dropna(subset=["_experiment_date"])
            frame = frame.drop_duplicates("_experiment_date", keep="last")
            frame = frame.set_index("_experiment_date").sort_index()
            required = {"Open", "High", "Low", "Close", "Volume"}
            if not required.issubset(frame.columns):
                raise ValueError(f"Prepared data for {symbol} is missing OHLCV columns")
            numeric = frame[list(required)].apply(pd.to_numeric, errors="coerce")
            if numeric.isna().any().any() or not all(
                math.isfinite(float(value))
                for value in numeric.to_numpy().ravel()
            ):
                raise ValueError(f"Prepared data for {symbol} contains missing or non-finite OHLCV values")
            if (numeric["Close"] <= 0).any() or (numeric["Open"] <= 0).any():
                raise ValueError(f"Prepared data for {symbol} contains non-positive prices")
            if (numeric["High"] < numeric["Low"]).any():
                raise ValueError(f"Prepared data for {symbol} contains invalid high/low values")
            frame[list(required)] = numeric
            frames[symbol] = frame
            date_sets.append(set(frame.index))

        benchmark = benchmark_data.copy()
        benchmark_date_column = benchmark.columns[0]
        benchmark["_experiment_date"] = pd.to_datetime(
            benchmark[benchmark_date_column], errors="coerce"
        ).dt.normalize()
        benchmark = benchmark.dropna(subset=["_experiment_date"])
        benchmark = benchmark.drop_duplicates("_experiment_date", keep="last")
        benchmark = benchmark.set_index("_experiment_date").sort_index()
        if "Close" not in benchmark:
            raise ValueError("Prepared benchmark data is missing Close")
        benchmark["Close"] = pd.to_numeric(benchmark["Close"], errors="coerce")
        if benchmark["Close"].isna().any() or not benchmark["Close"].map(math.isfinite).all():
            raise ValueError("Prepared benchmark Close contains missing or non-finite values")
        if (benchmark["Close"] <= 0).any():
            raise ValueError("Prepared benchmark contains non-positive closes")
        date_sets.append(set(benchmark.index))

        calendar_dates = pd.DatetimeIndex(sorted(set.union(*date_sets)))
        if len(calendar_dates) < 300:
            raise ValueError("Fewer than 300 portfolio calendar dates are available")

        aligned_stocks = {
            symbol: frame.reset_index(drop=True)
            for symbol, frame in frames.items()
        }
        aligned_benchmark = benchmark.reset_index(drop=True)
        return aligned_stocks, aligned_benchmark, calendar_dates

    @staticmethod
    def split_dates(
        dates: pd.DatetimeIndex,
        benchmark_dates: pd.DatetimeIndex | None = None,
    ) -> dict[str, Any]:
        # Preserve the one-argument helper behaviour for existing callers/tests.
        if benchmark_dates is None:
            benchmark_dates = dates
        if len(benchmark_dates) < 2:
            raise ValueError("Insufficient benchmark history for train/test split")

        benchmark_split_index = int(len(benchmark_dates) * StrategyExperimentService.SPLIT_RATIO)
        if benchmark_split_index <= 0 or benchmark_split_index >= len(benchmark_dates):
            raise ValueError("Insufficient benchmark history for train/test split")

        benchmark_split_date = pd.Timestamp(benchmark_dates[benchmark_split_index]).normalize()
        split_index = int(dates.get_indexer([benchmark_split_date])[0])
        if split_index < 0:
            raise ValueError("Benchmark split date is missing from the union calendar")
        if (
            split_index <= 252
            or len(dates) - split_index <= StrategyExperimentService.MAX_HOLD_DAYS
        ):
            raise ValueError("Insufficient aligned history for warm-up, train, and test periods")

        return {
            "split_index": split_index,
            "split_date": benchmark_split_date.date().isoformat(),
            "training_start": dates[0].date().isoformat(),
            "training_end": dates[split_index - 1].date().isoformat(),
            "test_start": dates[split_index].date().isoformat(),
            "test_end": dates[-1].date().isoformat(),
            "benchmark_training_end": pd.Timestamp(benchmark_dates[benchmark_split_index - 1]).date().isoformat(),
            "benchmark_test_start": benchmark_split_date.date().isoformat(),
        }

    @staticmethod
    def benchmark_return_on_dates(
        benchmark: pd.DataFrame,
        start_date: str | pd.Timestamp,
        end_date: str | pd.Timestamp,
    ) -> dict[str, Any]:
        if benchmark is None or benchmark.empty or "Close" not in benchmark:
            raise ValueError("Benchmark data with Close is required")

        requested_start = pd.Timestamp(start_date).normalize()
        requested_end = pd.Timestamp(end_date).normalize()
        if requested_start > requested_end:
            raise ValueError("Benchmark start date must not be after end date")

        date_column = benchmark.columns[0]
        dates = pd.to_datetime(benchmark[date_column], errors="coerce").dt.normalize()
        closes = pd.to_numeric(benchmark["Close"], errors="coerce")
        observations = pd.DataFrame({"date": dates, "close": closes})
        observations = observations.dropna(subset=["date", "close"])
        observations = observations[observations["close"] > 0]
        observations = observations[observations["close"].map(math.isfinite)]
        observations = observations.drop_duplicates("date", keep="last").sort_values("date")

        start_observation = observations[observations["date"] <= requested_start]
        end_observation = observations[observations["date"] <= requested_end]
        if start_observation.empty:
            raise ValueError("No valid benchmark close exists on or before test start")
        if end_observation.empty:
            raise ValueError("No valid benchmark close exists on or before test end")

        start = start_observation.iloc[-1]
        end = end_observation.iloc[-1]
        start_close = float(start["close"])
        end_close = float(end["close"])
        return {
            "test_start_close": start_close,
            "test_end_close": end_close,
            "actual_test_start": pd.Timestamp(start["date"]).isoformat(),
            "actual_test_end": pd.Timestamp(end["date"]).isoformat(),
            "test_return_pct": round((end_close / start_close - 1.0) * 100.0, 4),
        }

    @staticmethod
    def passes_thresholds(
        close: float,
        prior_high: float,
        ema200: float,
        breakout_distance_pct: float | None = None,
        ema200_distance_pct: float | None = None,
    ) -> bool:
        if prior_high <= 0 or ema200 <= 0:
            return False
        breakout_distance = (close / prior_high - 1.0) * 100.0
        ema_distance = (close / ema200 - 1.0) * 100.0
        tolerance = 1e-9
        if breakout_distance_pct is not None and breakout_distance + tolerance < breakout_distance_pct:
            return False
        if ema200_distance_pct is not None and ema_distance + tolerance < ema200_distance_pct:
            return False
        return True

    @staticmethod
    def size_order(
        entry_reference: float,
        atr: float,
        available_cash: float,
        assumptions: dict[str, float],
        settings: dict[str, Any],
    ) -> dict[str, Any]:
        slippage_rate = float(assumptions["slippage_bps"]) / 10000.0
        fee_rate = (
            float(assumptions["brokerage_pct"])
            + float(assumptions["transaction_cost_pct"])
        ) / 100.0
        entry_fill = float(entry_reference) * (1.0 + slippage_rate)
        risk = RiskManagementService.calculate_trade(
            entry_price=entry_fill,
            atr=float(atr),
            available_cash=float(available_cash),
            settings=settings,
        )
        per_share_outlay = entry_fill * (1.0 + fee_rate)
        cash_shares = int(available_cash // per_share_outlay) if per_share_outlay > 0 else 0
        shares = min(int(risk["position_size"]), cash_shares)
        return {
            "shares": shares,
            "entry_fill": entry_fill,
            "entry_cost": shares * per_share_outlay,
            "stop": float(risk["initial_stop"]),
            "risk": risk,
        }

    @staticmethod
    def _settings() -> dict[str, Any]:
        settings = dict(ConfigService.all())
        settings["atr_multiplier"] = StrategyExperimentService.STOP_ATR
        settings["target_rr"] = (
            StrategyExperimentService.TARGET_ATR / StrategyExperimentService.STOP_ATR
        )
        return settings

    @staticmethod
    def relative_volume_at(frame: pd.DataFrame, index: int) -> float | None:
        """Signal-day volume divided by the preceding 20 completed sessions' mean."""
        volume_lookback = 20
        if index < volume_lookback:
            return None
        signal_volume = float(frame["Volume"].iloc[index])
        preceding = frame["Volume"].iloc[index - volume_lookback:index]
        average_volume = float(preceding.mean())
        if not math.isfinite(signal_volume) or not math.isfinite(average_volume) or average_volume <= 0:
            return None
        return signal_volume / average_volume

    @staticmethod
    def prepare_relative_strength_benchmark(
        benchmark: pd.DataFrame,
        lookback: int = 63,
    ) -> dict[str, Any]:
        """Prepare NIFTY 63-session returns once for reuse across stock signals."""
        date_column = benchmark.columns[0]
        frame = benchmark.copy()
        frame["_experiment_date"] = pd.to_datetime(frame[date_column], errors="coerce").dt.normalize()
        frame["Close"] = pd.to_numeric(frame["Close"], errors="coerce")
        frame = frame.dropna(subset=["_experiment_date", "Close"])
        frame = frame[frame["Close"] > 0]
        frame = frame.drop_duplicates("_experiment_date", keep="last").sort_values("_experiment_date")

        dates = pd.DatetimeIndex(frame["_experiment_date"])
        returns: list[float | None] = [None] * len(frame)
        closes = frame["Close"].tolist()
        for index in range(lookback, len(frame)):
            past = float(closes[index - lookback])
            close = float(closes[index])
            if past > 0 and math.isfinite(past) and math.isfinite(close):
                returns[index] = (close / past - 1.0) * 100.0

        return {"dates": dates, "returns": returns}

    @staticmethod
    def relative_strength_vs_nifty(
        stock_frame: pd.DataFrame,
        stock_index: int,
        benchmark: pd.DataFrame,
        lookback: int = 63,
        prepared_benchmark: dict[str, Any] | None = None,
    ) -> float | None:
        """Stock 63-session return minus latest available NIFTY 63-session return."""
        if stock_index < lookback:
            return None

        stock_date = pd.Timestamp(stock_frame.iloc[stock_index, 0]).normalize()
        prepared = prepared_benchmark or StrategyExperimentService.prepare_relative_strength_benchmark(
            benchmark, lookback
        )
        benchmark_dates = prepared["dates"]
        benchmark_returns = prepared["returns"]

        latest_index = benchmark_dates.searchsorted(stock_date, side="right") - 1
        if latest_index < lookback:
            return None

        latest_benchmark_date = benchmark_dates[latest_index]
        if (stock_date - latest_benchmark_date).days > 5:
            return None

        benchmark_return = benchmark_returns[latest_index]
        if benchmark_return is None:
            return None

        stock_close = float(stock_frame["Close"].iloc[stock_index])
        stock_past = float(stock_frame["Close"].iloc[stock_index - lookback])
        if stock_close <= 0 or stock_past <= 0:
            return None

        stock_return = (stock_close / stock_past - 1.0) * 100.0
        if not all(math.isfinite(value) for value in (stock_return, benchmark_return)):
            return None
        return stock_return - benchmark_return

    @staticmethod
    def variant_passes(
        frame: pd.DataFrame,
        index: int,
        benchmark: pd.DataFrame,
        variant: dict[str, Any],
        prepared_benchmark_relative_strength: dict[str, Any] | None = None,
    ) -> bool:
        close = float(frame["Close"].iloc[index])
        prior_high = float(frame["High"].iloc[index - 55:index].max())
        ema200 = float(frame["EMA200"].iloc[index])
        if not StrategyExperimentService.passes_thresholds(
            close,
            prior_high,
            ema200,
            variant["breakout_distance_pct"],
            None,
        ):
            return False

        relative_volume = variant["relative_volume"]
        if relative_volume is not None:
            observed_volume = StrategyExperimentService.relative_volume_at(frame, index)
            if observed_volume is None or observed_volume + 1e-12 < relative_volume:
                return False

        relative_strength = variant["relative_strength_pct"]
        if relative_strength is not None:
            observed_strength = StrategyExperimentService.relative_strength_vs_nifty(
                frame,
                index,
                benchmark,
                prepared_benchmark=prepared_benchmark_relative_strength,
            )
            if observed_strength is None or observed_strength + 1e-9 < relative_strength:
                return False
        return True

    @staticmethod
    def _relative_strength_score(frame: pd.DataFrame, index: int) -> float:
        lookbacks = (
            int(ConfigService.get("relative_strength_3m_lookback", 63)),
            int(ConfigService.get("relative_strength_6m_lookback", 126)),
            int(ConfigService.get("relative_strength_12m_lookback", 252)),
        )
        if index < max(lookbacks):
            return float("-inf")
        current = float(frame["Close"].iloc[index])
        weights = (
            float(ConfigService.get("relative_strength_3m_weight", 0.3)),
            float(ConfigService.get("relative_strength_6m_weight", 0.3)),
            float(ConfigService.get("relative_strength_12m_weight", 0.4)),
        )
        score = 0.0
        for lookback, weight in zip(lookbacks, weights):
            past = float(frame["Close"].iloc[index - lookback])
            if past <= 0:
                return float("-inf")
            score += (current / past - 1.0) * 100.0 * weight
        return score

    @staticmethod
    def _signal_inputs_valid(
        frame: pd.DataFrame,
        index: int,
        breakout_lookback: int,
    ) -> bool:
        """Reject incomplete indicator or rolling-window inputs before signal generation."""
        volume_lookback = int(ConfigService.get("volume_lookback", 20))
        consolidation_lookback = int(ConfigService.get("consolidation_lookback", 10))
        required_history = max(
            200,
            breakout_lookback + 1,
            volume_lookback,
            consolidation_lookback + 1,
        )
        if index + 1 < required_history:
            return False

        latest = frame.iloc[index]
        required_values = (
            latest["Open"], latest["High"], latest["Low"], latest["Close"],
            latest["Volume"], latest["RSI"], latest["EMA50"],
            latest["EMA200"], latest["ATR"],
        )
        try:
            values = [float(value) for value in required_values]
        except (TypeError, ValueError):
            return False
        if not all(math.isfinite(value) for value in values):
            return False

        open_price, high, low, close, volume, rsi, ema50, ema200, atr = values
        if min(open_price, high, low, close, ema50, ema200, atr) <= 0 or volume < 0:
            return False
        if high < low or not 0 <= rsi <= 100:
            return False

        prior_high = frame["High"].iloc[index - breakout_lookback:index].max()
        average_volume = frame["Volume"].iloc[index - volume_lookback + 1:index + 1].mean()
        consolidation_high = frame["High"].iloc[index - consolidation_lookback:index].max()
        consolidation_low = frame["Low"].iloc[index - consolidation_lookback:index].min()
        rolling_values = (prior_high, average_volume, consolidation_high, consolidation_low)
        try:
            return all(math.isfinite(float(value)) for value in rolling_values)
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _prepare_frames(stock_frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        prepared = {}
        for symbol, source in stock_frames.items():
            frame = source.copy()
            frame["EMA20"] = TechnicalIndicators.calculate_ema(frame)
            frame["RSI"] = TechnicalIndicators.calculate_rsi(frame)
            frame["ATR"] = TechnicalIndicators.calculate_atr(frame)
            frame["EMA50"] = TechnicalIndicators.calculate_ema50(frame)
            frame["EMA200"] = TechnicalIndicators.calculate_ema200(frame)
            prepared[symbol] = frame
        return prepared

    @staticmethod
    def _regimes(benchmark: pd.DataFrame) -> list[bool | None]:
        ema50 = TechnicalIndicators.calculate_ema50(benchmark)
        ema200 = TechnicalIndicators.calculate_ema200(benchmark)
        return [
            MarketRegimeService.is_bullish_ema(fast, slow)
            for fast, slow in zip(ema50, ema200)
        ]

    @staticmethod
    def _metric_summary(
        equity_curve: list[dict[str, Any]],
        trades: list[dict[str, Any]],
        starting_capital: float,
        max_concurrent_positions: int = 0,
        per_stock_attribution: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        pnls = [float(trade["net_pnl"]) for trade in trades]
        wins = [pnl for pnl in pnls if pnl > 0]
        losses = [pnl for pnl in pnls if pnl < 0]
        gross_wins = sum(wins)
        gross_losses = abs(sum(losses))
        ending_equity = float(equity_curve[-1]["equity"]) if equity_curve else starting_capital
        peak = starting_capital
        max_drawdown = 0.0
        for point in equity_curve:
            equity = float(point["equity"])
            peak = max(peak, equity)
            if peak > 0:
                max_drawdown = min(max_drawdown, (equity / peak - 1.0) * 100.0)

        average_exposure = (
            sum(float(point["exposure_pct"]) for point in equity_curve) / len(equity_curve)
            if equity_curve else 0.0
        )
        maximum_exposure = max(
            (float(point["exposure_pct"]) for point in equity_curve),
            default=0.0,
        )
        average_cash_utilization = (
            sum(float(point["cash_utilization_pct"]) for point in equity_curve) / len(equity_curve)
            if equity_curve else 0.0
        )
        maximum_cash_utilization = max(
            (float(point["cash_utilization_pct"]) for point in equity_curve),
            default=0.0,
        )

        quarterly_groups: dict[str, list[dict[str, Any]]] = {}
        for point in equity_curve:
            period = pd.Timestamp(point["date"]).to_period("Q")
            quarter = f"{period.year}-Q{period.quarter}"
            quarterly_groups.setdefault(quarter, []).append(point)
        quarterly_summaries = []
        prior_equity = float(starting_capital)
        for quarter, points in quarterly_groups.items():
            quarter_peak = prior_equity
            quarter_drawdown = 0.0
            for point in points:
                equity = float(point["equity"])
                quarter_peak = max(quarter_peak, equity)
                if quarter_peak > 0:
                    quarter_drawdown = min(quarter_drawdown, (equity / quarter_peak - 1.0) * 100.0)
            ending_quarter_equity = float(points[-1]["equity"])
            quarterly_summaries.append({
                "quarter": quarter,
                "start_equity": round(prior_equity, 2),
                "end_equity": round(ending_quarter_equity, 2),
                "return_pct": round((ending_quarter_equity / prior_equity - 1.0) * 100.0, 4)
                if prior_equity else 0.0,
                "maximum_drawdown_pct": round(quarter_drawdown, 4),
                "sessions": len(points),
            })
            prior_equity = ending_quarter_equity

        return {
            "trade_count": len(trades),
            "win_rate_pct": round(len(wins) / len(trades) * 100.0, 4) if trades else 0.0,
            "net_expectancy": round(sum(pnls) / len(pnls), 4) if pnls else 0.0,
            "profit_factor": round(gross_wins / gross_losses, 4) if gross_losses else None,
            "net_return_pct": round((ending_equity / starting_capital - 1.0) * 100.0, 4) if starting_capital else 0.0,
            "maximum_drawdown_pct": round(max_drawdown, 4),
            "average_exposure_pct": round(average_exposure, 4),
            "maximum_exposure_pct": round(maximum_exposure, 4),
            "average_cash_utilization_pct_of_starting_capital": round(average_cash_utilization, 4),
            "maximum_cash_utilization_pct_of_starting_capital": round(maximum_cash_utilization, 4),
            "max_concurrent_positions": max_concurrent_positions,
            "ending_equity": round(ending_equity, 2),
            "trades": trades,
            "equity_curve": equity_curve,
            "quarterly_summaries": quarterly_summaries,
            "per_stock_attribution": per_stock_attribution or {},
        }

    @staticmethod
    def _simulate_period(
        frames: dict[str, pd.DataFrame],
        benchmark: pd.DataFrame,
        regimes: list[bool | None],
        start_index: int,
        end_index: int,
        starting_capital: float,
        variant: dict[str, Any] | None = None,
        require_full_holding_window: bool = True,
    ) -> dict[str, Any]:
        cash = float(starting_capital)
        settings = StrategyExperimentService._settings()
        max_positions = max(0, int(settings.get("max_positions", 8)))
        assumptions = BacktestService.cost_assumptions()
        fee_rate = (
            float(assumptions["brokerage_pct"])
            + float(assumptions["transaction_cost_pct"])
        ) / 100.0
        slippage_rate = float(assumptions["slippage_bps"]) / 10000.0
        positions: dict[str, dict[str, Any]] = {}
        pending: list[dict[str, Any]] = []
        trades: list[dict[str, Any]] = []
        equity_curve: list[dict[str, Any]] = []
        max_concurrent_positions = 0
        calendar_dates = sorted({
            date
            for frame in frames.values()
            for date in pd.to_datetime(frame.iloc[:, 0], errors="coerce").dt.normalize()
            if pd.notna(date)
        } | {
            date
            for date in pd.to_datetime(benchmark.iloc[:, 0], errors="coerce").dt.normalize()
            if pd.notna(date)
        })
        if start_index < 0 or end_index > len(calendar_dates) or start_index >= end_index:
            raise ValueError("Simulation date indices are outside the union calendar")
        period_dates = calendar_dates[start_index:end_index]
        period_start = period_dates[0]
        period_end = period_dates[-1]
        stock_dates = {
            symbol: pd.DatetimeIndex(
                pd.to_datetime(frame.iloc[:, 0], errors="coerce").dt.normalize()
            )
            for symbol, frame in frames.items()
        }
        stock_indices = {
            symbol: {date: index for index, date in enumerate(dates) if pd.notna(date)}
            for symbol, dates in stock_dates.items()
        }
        benchmark_dates = pd.DatetimeIndex(
            pd.to_datetime(benchmark.iloc[:, 0], errors="coerce").dt.normalize()
        )
        pending_by_date: dict[pd.Timestamp, list[dict[str, Any]]] = {}
        last_closes: dict[str, float] = {}
        last_regime: bool | None = None
        breakout_lookback = int(ConfigService.get("breakout_lookback", 55))
        prepared_relative_strength = StrategyExperimentService.prepare_relative_strength_benchmark(
            benchmark, 63
        )

        for date in period_dates:
            benchmark_index = benchmark_dates.searchsorted(date, side="right") - 1
            if benchmark_index >= 0:
                last_regime = regimes[benchmark_index]

            # Fill pending orders only at each stock's next actual session open.
            for candidate in pending_by_date.pop(date, []):
                symbol = candidate["symbol"]
                if symbol in positions or len(positions) >= max_positions:
                    continue
                frame = frames[symbol]
                local_index = stock_indices[symbol].get(date)
                if local_index is None:
                    continue
                raw_entry = float(frame["Open"].iloc[local_index])
                sized = StrategyExperimentService.size_order(
                    raw_entry,
                    candidate["atr"],
                    cash,
                    assumptions,
                    settings,
                )
                shares = sized["shares"]
                if shares <= 0 or sized["entry_cost"] > cash + 1e-8:
                    continue
                cash -= sized["entry_cost"]
                positions[symbol] = {
                    "entry_index": local_index,
                    "bars_held": 0,
                    "entry_date": frame.iloc[:, 0].iloc[local_index],
                    "reference_entry": raw_entry,
                    "entry_fill": sized["entry_fill"],
                    "shares": shares,
                    "entry_cost": sized["entry_cost"],
                    "atr": float(candidate["atr"]),
                    "active_stop": sized["stop"],
                    "active_stop_reason": "stop-loss",
                    "target": sized["entry_fill"] + StrategyExperimentService.TARGET_ATR * float(candidate["atr"]),
                    "highest_close": sized["entry_fill"],
                }
                last_closes[symbol] = float(frame["Close"].iloc[local_index])
                max_concurrent_positions = max(max_concurrent_positions, len(positions))

            # Process exits and close-confirmed stop changes only when that symbol traded.
            for symbol in list(positions):
                local_index = stock_indices[symbol].get(date)
                if local_index is None:
                    continue
                position = positions[symbol]
                frame = frames[symbol]
                open_price = float(frame["Open"].iloc[local_index])
                high = float(frame["High"].iloc[local_index])
                low = float(frame["Low"].iloc[local_index])
                close = float(frame["Close"].iloc[local_index])
                position["bars_held"] += 1
                exit_reference = None
                exit_reason = None
                if low <= position["active_stop"]:
                    exit_reference = min(position["active_stop"], open_price)
                    exit_reason = position["active_stop_reason"]
                elif high >= position["target"]:
                    exit_reference = position["target"]
                    exit_reason = "target"
                elif position["bars_held"] >= StrategyExperimentService.MAX_HOLD_DAYS:
                    exit_reference = close
                    exit_reason = "time_exit"

                if exit_reference is not None:
                    execution = BacktestService.calculate_execution_costs(
                        position["reference_entry"], exit_reference, assumptions
                    )
                    exit_fill = execution["exit_fill_price"]
                    proceeds = position["shares"] * exit_fill * (1.0 - fee_rate)
                    cash += proceeds
                    trades.append({
                        "symbol": symbol,
                        "entry_date": str(position["entry_date"]),
                        "exit_date": str(frame.iloc[:, 0].iloc[local_index]),
                        "shares": position["shares"],
                        "net_pnl": proceeds - position["entry_cost"],
                        "net_return_pct": execution["net_return_pct"],
                        "exit_reason": exit_reason,
                    })
                    del positions[symbol]
                    last_closes[symbol] = close
                    continue

                position["highest_close"] = max(position["highest_close"], close)
                if position["highest_close"] >= position["entry_fill"] + 2.0 * position["atr"]:
                    if position["entry_fill"] > position["active_stop"]:
                        position["active_stop"] = position["entry_fill"]
                        position["active_stop_reason"] = "trailing stop"
                trail_stop = position["highest_close"] - StrategyExperimentService.TRAIL_ATR * float(frame["ATR"].iloc[local_index])
                if math.isfinite(trail_stop) and trail_stop > position["active_stop"]:
                    position["active_stop"] = trail_stop
                    position["active_stop_reason"] = "trailing stop"
                last_closes[symbol] = close

            invested_market_value = sum(
                position["shares"] * last_closes.get(symbol, position["reference_entry"])
                for symbol, position in positions.items()
            )
            equity = cash + invested_market_value
            if date == period_end:
                liquidation_market_value = 0.0
                for symbol, position in positions.items():
                    close = float(last_closes.get(symbol, position["reference_entry"]))
                    execution = BacktestService.calculate_execution_costs(
                        position["reference_entry"], close, assumptions
                    )
                    liquidated = position["shares"] * execution["exit_fill_price"] * (1.0 - fee_rate)
                    liquidation_market_value += liquidated
                equity = cash + liquidation_market_value
                invested_market_value = liquidation_market_value
            equity_curve.append({
                "date": date.isoformat(),
                "cash": round(cash, 2),
                "invested_market_value": round(invested_market_value, 2),
                "equity": round(equity, 2),
                "exposure_pct": invested_market_value / equity * 100.0 if equity else 0.0,
                "cash_utilization_pct": invested_market_value / starting_capital * 100.0 if starting_capital else 0.0,
            })

            if date == period_end or last_regime is not True:
                continue
            ranked = []
            for symbol, frame in frames.items():
                if symbol in positions:
                    continue
                local_index = stock_indices[symbol].get(date)
                if local_index is None or local_index < 252:
                    continue
                if not StrategyExperimentService._signal_inputs_valid(
                    frame, local_index, breakout_lookback
                ):
                    continue
                sample = frame.iloc[:local_index + 1]
                signal = BreakoutStrategy.generate_signal(sample)
                if signal.get("signal") != "BUY":
                    continue
                active_variant = variant or StrategyExperimentService.VARIANTS["baseline"]
                if not StrategyExperimentService.variant_passes(
                    frame,
                    local_index,
                    benchmark,
                    active_variant,
                    prepared_relative_strength,
                ):
                    continue
                atr = float(frame["ATR"].iloc[local_index])
                if not math.isfinite(atr) or atr <= 0:
                    continue
                entry_local_index = local_index + 1
                if entry_local_index >= len(frame):
                    continue
                entry_date = stock_dates[symbol][entry_local_index]
                if entry_date > period_end:
                    continue
                if require_full_holding_window:
                    last_exit_local_index = (
                        entry_local_index + StrategyExperimentService.MAX_HOLD_DAYS - 1
                    )
                    if last_exit_local_index >= len(frame):
                        continue
                    last_exit_date = stock_dates[symbol][last_exit_local_index]
                    if last_exit_date > period_end:
                        continue
                score = StrategyExperimentService._relative_strength_score(frame, local_index)
                ranked.append({"symbol": symbol, "score": score, "atr": atr, "entry_date": entry_date})
            ranked.sort(key=lambda item: (-item["score"], item["symbol"]))
            for candidate in ranked:
                pending_by_date.setdefault(candidate["entry_date"], []).append(candidate)

        attribution: dict[str, dict[str, Any]] = {}
        for trade in trades:
            row = attribution.setdefault(trade["symbol"], {
                "completed_trades": 0,
                "wins": 0,
                "losses": 0,
                "realized_net_pnl": 0.0,
            })
            pnl = float(trade["net_pnl"])
            row["completed_trades"] += 1
            row["wins"] += int(pnl > 0)
            row["losses"] += int(pnl < 0)
            row["realized_net_pnl"] += pnl

        if end_index > 0:
            for symbol, position in positions.items():
                close = float(last_closes.get(symbol, position["reference_entry"]))
                execution = BacktestService.calculate_execution_costs(
                    position["reference_entry"], close, assumptions
                )
                exit_fill = execution["exit_fill_price"]
                marked_proceeds = position["shares"] * exit_fill * (1.0 - fee_rate)
                row = attribution.setdefault(symbol, {
                    "completed_trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "realized_net_pnl": 0.0,
                })
                row["open_shares"] = position["shares"]
                row["ending_market_value"] = round(
                    position["shares"] * exit_fill * (1.0 - fee_rate), 2
                )
                row["unrealized_net_pnl_at_liquidation"] = round(
                    marked_proceeds - position["entry_cost"], 2
                )
        for row in attribution.values():
            row["realized_net_pnl"] = round(row["realized_net_pnl"], 2)
            row["total_net_pnl_at_test_end"] = round(
                row["realized_net_pnl"] + row.get("unrealized_net_pnl_at_liquidation", 0.0),
                2,
            )

        return StrategyExperimentService._metric_summary(
            equity_curve,
            trades,
            starting_capital,
            max_concurrent_positions,
            attribution,
        )

    @staticmethod
    def run_experiment(
        stock_data: dict[str, pd.DataFrame],
        benchmark_data: pd.DataFrame,
        split_date: str | pd.Timestamp | None = None,
    ) -> dict[str, Any]:
        aligned_stocks, benchmark, dates = StrategyExperimentService.align_prepared_data(
            stock_data, benchmark_data
        )
        benchmark_dates = pd.DatetimeIndex(
            pd.to_datetime(benchmark.iloc[:, 0], errors="coerce").dt.normalize()
        )
        split = StrategyExperimentService.split_dates(dates, benchmark_dates)
        if split_date is not None:
            requested_split = pd.Timestamp(split_date).normalize()
            benchmark_matches = benchmark_dates.get_indexer([requested_split])
            if benchmark_matches[0] < 0:
                raise ValueError("Explicit split date must exist on the benchmark trading calendar")
            union_matches = dates.get_indexer([requested_split])
            if union_matches[0] < 0:
                raise ValueError("Explicit benchmark split date is missing from the union calendar")
            split_index = int(union_matches[0])
            if (
                split_index <= 252
                or len(dates) - split_index <= StrategyExperimentService.MAX_HOLD_DAYS
            ):
                raise ValueError("Explicit split date leaves insufficient train or test history")
            benchmark_index = int(benchmark_matches[0])
            split = {
                "split_index": split_index,
                "split_date": requested_split.date().isoformat(),
                "training_start": dates[0].date().isoformat(),
                "training_end": dates[split_index - 1].date().isoformat(),
                "test_start": dates[split_index].date().isoformat(),
                "test_end": dates[-1].date().isoformat(),
                "benchmark_training_end": benchmark_dates[benchmark_index - 1].date().isoformat(),
                "benchmark_test_start": requested_split.date().isoformat(),
            }
        split_index = split["split_index"]
        frames = StrategyExperimentService._prepare_frames(aligned_stocks)
        regimes = StrategyExperimentService._regimes(benchmark)
        starting_capital = float(ConfigService.get("capital", 100000))
        test_results = {}
        for variant_key, variant in StrategyExperimentService.VARIANTS.items():
            test_results[variant_key] = StrategyExperimentService._simulate_period(
                frames,
                benchmark,
                regimes,
                split_index,
                len(dates),
                starting_capital,
                variant,
                require_full_holding_window=False,
            )

        benchmark_result = StrategyExperimentService.benchmark_return_on_dates(
            benchmark,
            split["test_start"],
            split["test_end"],
        )
        is_static_nifty100_subset = set(frames).issubset(set(NIFTY_100))
        return {
            "periods": {
                **split,
                "aligned_sessions": len(dates),
                "symbols": sorted(frames),
            },
            "universe_metadata": {
                "source": (
                    "current static NIFTY_100 list (or subset)"
                    if is_static_nifty100_subset
                    else "caller-supplied prepared data"
                ),
                "matches_current_static_nifty_100": set(frames) == set(NIFTY_100),
                "historical_constituent_membership_available": False,
                "survivorship_bias_warning": (
                    "Current static NIFTY_100 membership is an exploratory approximation with "
                    "survivorship bias; historical constituents are not present in project sources."
                    if is_static_nifty100_subset
                    else "Prepared universe membership is unverified and may be survivorship-biased."
                ),
            },
            "benchmark": {
                "symbol": "^NSEI",
                **benchmark_result,
            },
            "variants": {
                key: value
                for key, value in StrategyExperimentService.VARIANTS.items()
            },
            "test_results": test_results,
            "selection_rule": {
                "method": "six fixed variants; no threshold optimization",
                "training_period_used": "chronological warm-up and 70% split define identical shared windows; no training threshold selection",
            },
        }