import copy
import time
from datetime import datetime

from app.services.market_regime_service import (
    MarketRegimeService
)

from app.services.relative_strength_service import (
    RelativeStrengthService
)

from app.services.trading_service import (
    TradingService
)

from app.services.portfolio_service import (
    PortfolioService
)

from app.engines.decision_engine import (
    DecisionEngine
)

from app.core.review_history import (
    ReviewHistory
)

from app.services.review_comparison_service import (
    ReviewComparisonService
)

from app.services.position_service import (
    PositionService
)

from app.services.risk_management_service import (
    RiskManagementService
)

from app.services.review_summary_service import (
    ReviewSummaryService
)

from app.services.alert_service import (
    AlertService
)

from app.core.config_service import (
    ConfigService
)

from app.core.logger import (
    LoggerService
)


class ReviewService:

    @staticmethod
    def _build_trade_plan_item(analysis):
        decision = analysis.get("decision") or {}
        action = decision.get("action", "WATCHLIST")
        risk = analysis.get("risk") or {}
        is_new_buy = action == "BUY"

        entry_price = (
            analysis.get("close_price")
            if is_new_buy
            else analysis.get("entry_price")
        )
        stop_loss = (
            risk.get("initial_stop")
            if is_new_buy
            else analysis.get("current_stop")
        )
        target = (
            risk.get("target_price")
            if is_new_buy
            else analysis.get("target_price")
        )
        quantity = (
            risk.get("position_size", 0)
            if is_new_buy
            else analysis.get("quantity", 0)
        )
        capital_allocation = (
            risk.get("capital_required", 0)
            if is_new_buy
            else analysis.get("market_value", 0)
        )
        estimated_risk = (
            risk.get("estimated_risk_amount", 0)
            if is_new_buy
            else max(0.0, float(entry_price or 0) - float(stop_loss or 0))
            * float(quantity or 0)
        )

        return {
            "symbol": analysis.get("symbol"),
            "decision": action,
            "entry_price": entry_price,
            "entry_condition": (
                (analysis.get("signal") or {}).get("reason")
                if action in {"BUY", "WATCHLIST"}
                else None
            ),
            "quantity": quantity,
            "stop_loss": stop_loss,
            "target": target,
            "proposed_capital_allocation": capital_allocation,
            "estimated_risk_amount": estimated_risk,
            "reason": decision.get("reason", ""),
        }

    @staticmethod
    def get_latest_review():
        history = ReviewHistory.load()
        if history:
            return copy.deepcopy(history[-1])
        return ReviewService.generate_review()

    @staticmethod
    def generate_review():

        total_start = time.perf_counter()
        LoggerService.info("Review Start")
        start_time = datetime.now()

        stage_start = time.perf_counter()
        regime = (
            MarketRegimeService
            .get_market_regime()
        )
        LoggerService.info(
            f"Stage MarketRegimeService completed in {(time.perf_counter() - stage_start):.3f}s"
        )

        stage_start = time.perf_counter()
        all_rankings = (
            RelativeStrengthService.get_rankings(
                return_data=True
            )
        )
        LoggerService.info(
            f"Stage RelativeStrengthService completed in {(time.perf_counter() - stage_start):.3f}s"
        )

        max_candidates = ConfigService.get("relative_strength_count", 20)

        # Top candidates for new opportunities
        top_stocks = sorted(

            all_rankings,

            key=lambda x: x["score"],

            reverse=True

        )[:max_candidates]

        portfolio = (
            PortfolioService.load()
        )

        owned_positions = (
            PortfolioService.get_positions()
        )

        owned_symbols = {

            position.get("symbol")

            for position in owned_positions

            if position.get("symbol")

        }

        ranked_by_symbol = {

            stock["symbol"]: stock

            for stock in all_rankings

        }

        review_symbols = list(dict.fromkeys(
            [stock["symbol"] for stock in top_stocks]
            + sorted(owned_symbols)
        ))

        stage_start = time.perf_counter()
        review_stocks = [

            ranked_by_symbol[symbol]

            for symbol in review_symbols

            if symbol in ranked_by_symbol

        ]
        LoggerService.info(
            f"Stage Review stock selection completed in {(time.perf_counter() - stage_start):.3f}s"
        )

        buy = []

        hold = []

        exit_list = []

        watchlist = []
        trade_plan = []
        remaining_cash = float(portfolio.get("cash", 0) or 0)
        max_positions = max(0, int(ConfigService.get("max_positions", 8)))
        remaining_position_slots = max(0, max_positions - len(owned_positions))

        analysis_by_symbol = {}

        stage_start = time.perf_counter()
        for stock in review_stocks:

            symbol = stock["symbol"]

            df = stock["df"]

            analysis_start = time.perf_counter()
            analysis = (
                TradingService
                .analyze_stock(
                    symbol=symbol,
                    df=df
                )
            )
            LoggerService.info(
                f"Stage TradingService.analyze_stock {symbol} completed in {(time.perf_counter() - analysis_start):.3f}s"
            )

            owned = symbol in owned_symbols

            existing_position = None
            holding_metrics = None
            exit_reason = None
            if owned:
                existing_position = PositionService.normalize_position(
                    PortfolioService.get_position(symbol)
                )
                holding_metrics = PositionService.calculate_position_metrics(
                    existing_position,
                    analysis,
                )
                holding_health = PositionService.calculate_position_health(
                    existing_position,
                    analysis,
                    holding_metrics,
                )
                current_price = holding_metrics["current_price"]
                ema200 = analysis.get("ema200")
                current_stop = holding_metrics.get("current_stop")

                if holding_health == "Exit Candidate":
                    if ema200 is not None and current_price < float(ema200):
                        exit_reason = "Price below EMA200"
                    elif current_stop is not None and current_price < float(current_stop):
                        exit_reason = "Price below current trailing stop"

                analysis.update({
                    "holding_health": holding_health,
                    "entry_price": existing_position.get("entry_price"),
                    "quantity": existing_position.get("quantity", 0),
                    "target_price": existing_position.get("target_price"),
                    "current_stop": current_stop,
                    "market_value": holding_metrics["market_value"],
                    "profit_amount": holding_metrics["profit_amount"],
                    "profit_pct": holding_metrics["profit_pct"],
                })

            decision = (
                DecisionEngine.decide(
                    symbol=symbol,
                    signal=analysis["signal"]["signal"],
                    owned=owned,
                    market_regime=regime,
                    exit_reason=exit_reason,
                )
            )

            analysis["decision"] = decision

            analysis["relative_strength"] = (
                stock["score"]
            )

            analysis_by_symbol[symbol] = analysis

            if decision["action"] == "BUY":

                LoggerService.info(f"BUY {symbol}")

                if remaining_position_slots <= 0:
                    decision = {
                        "action": "WATCHLIST",
                        "reason": "Maximum open-position limit reached",
                    }
                    analysis["decision"] = decision
                    watchlist.append(analysis)
                else:
                    analysis["risk"] = RiskManagementService.calculate_trade(
                        entry_price=analysis.get("close_price"),
                        atr=analysis.get("atr"),
                        available_cash=remaining_cash,
                        settings=ConfigService.all(),
                    )
                    risk = analysis["risk"]
                    analysis["position_sizing"] = {
                        "risk_capital": risk["risk_amount"],
                        "risk_per_share": risk["risk_per_share"],
                        "shares": risk["position_size"],
                        "capital_required": risk["capital_required"],
                        "capital_available": remaining_cash,
                        "position_size_pct": risk["allocation_pct"],
                    }

                    if risk["position_size"] <= 0:
                        decision = {
                            "action": "WATCHLIST",
                            "reason": "Available cash cannot fund one share within the configured risk limit",
                        }
                        analysis["decision"] = decision
                        watchlist.append(analysis)
                    else:
                        remaining_cash -= risk["capital_required"]
                        remaining_position_slots -= 1
                        buy.append(analysis)

            elif decision["action"] == "HOLD":

                LoggerService.info(f"HOLD {symbol}")

                hold.append(analysis)

            elif decision["action"] == "EXIT":

                LoggerService.warning(f"SELL {symbol}")

                exit_list.append(analysis)

            else:

                watchlist.append(analysis)

            trade_plan.append(ReviewService._build_trade_plan_item(analysis))

        LoggerService.info(
            f"Stage Decision engine + per-stock analysis completed in {(time.perf_counter() - stage_start):.3f}s"
        )

        stage_start = time.perf_counter()
        for position in portfolio["positions"]:

            symbol = position.get("symbol")

            if not symbol:
                continue

            current_analysis = analysis_by_symbol.get(symbol)

            if current_analysis is None:
                continue

            entry_price = float(position.get("entry_price", 0) or 0)
            current_price = float(
                current_analysis.get("close_price", entry_price) or entry_price
            )
            highest_price = float(
                position.get("highest_price", entry_price) or entry_price
            )

            if current_price > highest_price:
                highest_price = current_price

            position["highest_price"] = highest_price

            position["highest_profit_pct"] = round(
                ((highest_price - entry_price) / entry_price * 100)
                if entry_price
                else 0.0,
                2
            )

            position["max_drawdown_pct"] = round(
                (
                    ((highest_price - current_price) / highest_price * 100)
                    if highest_price and current_price < highest_price
                    else 0.0
                ),
                2
            )

            atr = current_analysis.get("atr")

            position["current_stop"] = PositionService.calculate_trailing_stop(
                position,
                current_price=current_price,
                atr=atr,
            )

        PortfolioService.save(portfolio)
        LoggerService.info("Portfolio Update")
        LoggerService.info(
            f"Stage Portfolio analysis completed in {(time.perf_counter() - stage_start):.3f}s"
        )

        watchlist = sorted(

            watchlist,

            key=lambda x: (

                x["readiness_score"],

                x["relative_strength"]

            ),

            reverse=True

        )

        full_watchlist = watchlist.copy()

        for item in hold:

            symbol = item.get("symbol")

            if not symbol:
                continue

            position = (
                PortfolioService
                .get_position(symbol)
            )

            normalized_position = (
                PositionService
                .normalize_position(position)
            )

            metrics = (
                PositionService
                .calculate_position_metrics(
                    normalized_position,
                    item
                )
            )

            health = (
                PositionService
                .calculate_position_health(
                    normalized_position,
                    item,
                    metrics
                )
            )

            item.update({
                "holding_health": health,
                "days_held": metrics["days_held"],
                "profit_pct": metrics["profit_pct"],
                "profit_amount": metrics["profit_amount"],
                "market_value": metrics["market_value"],
                "drawdown_from_peak": metrics["drawdown_from_peak"],
                "highest_price": metrics["highest_price"],
                "current_stop": metrics["current_stop"],
                "comment": PositionService.generate_position_comment(
                    health,
                    {
                        "current_price": metrics["current_price"],
                        "ema20": item.get("ema20"),
                        "ema50": item.get("ema50"),
                        "ema200": item.get("ema200"),
                        "rsi": item.get("rsi"),
                        "relative_strength": item.get("relative_strength"),
                        "current_stop": metrics["current_stop"]
                    }
                )
            })

        open_holdings = hold + exit_list

        market_value = sum(
            float(position.get("market_value", 0) or 0)
            for position in open_holdings
        )

        unrealized_pnl = sum(
            float(position.get("profit_amount", 0) or 0)
            for position in open_holdings
        )

        portfolio_value = float(portfolio.get("cash", 0) or 0) + market_value

        cash = float(portfolio.get("cash", 0) or 0)

        cash_percent = (
            (cash / portfolio_value) * 100
            if portfolio_value else 0.0
        )

        invested_percent = (
            (market_value / portfolio_value) * 100
            if portfolio_value else 0.0
        )

        largest_position = None

        if open_holdings:
            largest_position = max(
            open_holdings,
                key=lambda x: float(x.get("market_value", 0) or 0)
            )
            largest_position = {
                "symbol": largest_position.get("symbol"),
                "market_value": float(
                    largest_position.get("market_value", 0) or 0
                )
            }

        largest_gain = max(
            [
                float(position.get("profit_amount", 0) or 0)
                for position in open_holdings
            ] + [0.0],
            default=0.0
        )

        largest_loss = min(
            [
                float(position.get("profit_amount", 0) or 0)
                for position in open_holdings
            ] + [0.0],
            default=0.0
        )

        review = {

            "market_regime": regime,

            "buy": buy,

            "hold": hold,

            "exit": exit_list,

            "trade_plan": trade_plan,

            "watchlist": watchlist[:10],

            "full_watchlist": full_watchlist,

            "portfolio_summary": {

                "cash": cash,
                "positions": len(
                    portfolio["positions"]
                ),
                "portfolio_value": portfolio_value,
                "market_value": market_value,
                "unrealized_pnl": unrealized_pnl,
                "cash_percent": cash_percent,
                "invested_percent": invested_percent,
                "largest_position": largest_position,
                "largest_gain": largest_gain,
                "largest_loss": largest_loss

            }

        }

        review["review_date"] = (
            datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            )
        )

        LoggerService.info("Review End")
        LoggerService.timing("ReviewService.generate_review", start_time)

        watchlist_size = ConfigService.get("watchlist_size", 10)
        review["watchlist"] = review["watchlist"][:watchlist_size]

        history = ReviewHistory.load()

        previous = (

            history[-1]

            if history

            else None

        )

        comparison = (

            ReviewComparisonService.compare(

                previous,

                review

            )

        )

        holding_changes = []

        if previous is not None:

            previous_hold = {
                item.get("symbol"): item
                for item in previous.get("hold", [])
                if item.get("symbol")
            }

            current_hold = {
                item.get("symbol"): item
                for item in review.get("hold", [])
                if item.get("symbol")
            }

            for symbol in sorted(
                set(previous_hold) & set(current_hold)
            ):

                previous_health = previous_hold[symbol].get("holding_health")
                current_health = current_hold[symbol].get("holding_health")

                if previous_health and current_health and previous_health != current_health:

                    holding_changes.append({
                        "symbol": symbol,
                        "from": previous_health,
                        "to": current_health,
                        "reason": PositionService.get_health_change_reason(
                            previous_health,
                            current_health,
                            current_hold[symbol]
                        )
                    })

        comparison["holding_changes"] = holding_changes
        review["changes"] = comparison

        stage_start = time.perf_counter()
        review["summary"] = ReviewSummaryService.generate(review)
        LoggerService.info(
            f"Stage Summary generation completed in {(time.perf_counter() - stage_start):.3f}s"
        )

        stage_start = time.perf_counter()
        review["alerts"] = AlertService.generate(review)
        LoggerService.info(
            f"Stage Alert generation completed in {(time.perf_counter() - stage_start):.3f}s"
        )

        LoggerService.info_event(
            "review_generated",
            market_regime=regime,
            buy_count=len(buy),
            hold_count=len(hold),
            exit_count=len(exit_list),
            watchlist_count=len(watchlist[:10]),
            summary=review["summary"],
        )

        stage_start = time.perf_counter()
        ReviewHistory.append(review)
        LoggerService.info(
            f"Stage Review history persisted completed in {(time.perf_counter() - stage_start):.3f}s"
        )

        review.pop(
            "full_watchlist",
            None
        )

        total_elapsed = time.perf_counter() - total_start
        LoggerService.info(f"Total ReviewService.generate_review execution time: {total_elapsed:.3f}s")
        LoggerService.timing("ReviewService.generate_review", start_time)
        return review