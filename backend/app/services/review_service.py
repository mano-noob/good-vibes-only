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

from app.services.trade_journal_service import (
    TradeJournalService
)

from app.services.risk_management_service import (
    RiskManagementService
)

from app.core.config_service import (
    ConfigService
)

from app.core.logger import (
    LoggerService
)


class ReviewService:

    @staticmethod
    def generate_review():

        LoggerService.info("Review Start")
        start_time = datetime.now()

        regime = (
            MarketRegimeService
            .get_market_regime()
        )

        # ---------------------------------
        # GET ALL RANKINGS
        # ---------------------------------

        all_rankings = (
            RelativeStrengthService.get_rankings(
                return_data=True
            )
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

        # ---------------------------------
        # INCLUDE OWNED STOCKS EVEN IF
        # OUTSIDE TOP 20
        # ---------------------------------

        ranked_by_symbol = {

            stock["symbol"]: stock

            for stock in all_rankings

        }

        review_symbols = {

            stock["symbol"]

            for stock in top_stocks

        }

        review_symbols.update(
            owned_symbols
        )

        review_stocks = [

            ranked_by_symbol[symbol]

            for symbol in review_symbols

            if symbol in ranked_by_symbol

        ]

        buy = []

        hold = []

        exit_list = []

        watchlist = []

        analysis_by_symbol = {}

        # ---------------------------------
        # ANALYSE STOCKS
        # ---------------------------------

        for stock in review_stocks:

            symbol = stock["symbol"]

            df = stock["df"]

            analysis = (
                TradingService
                .analyze_stock(
                    symbol=symbol,
                    df=df
                )
            )

            owned = (
                PortfolioService
                .is_owned(symbol)
            )

            decision = (
                DecisionEngine.decide(
                    symbol=symbol,
                    signal=analysis["signal"]["signal"],
                    owned=owned,
                    market_regime=regime
                )
            )

            analysis["decision"] = decision

            analysis["relative_strength"] = (
                stock["score"]
            )

            analysis_by_symbol[symbol] = analysis

            # ---------------------------------
            # ROUTE DECISION
            # ---------------------------------

            if decision["action"] == "BUY":

                LoggerService.info(f"BUY {symbol}")

                analysis["risk"] = RiskManagementService.calculate_trade(
                    entry_price=analysis.get("close_price"),
                    atr=analysis.get("atr"),
                    available_cash=float(portfolio.get("cash", 0) or 0),
                    settings=ConfigService.all()
                )

                buy.append(analysis)

            elif decision["action"] == "HOLD":

                LoggerService.info(f"HOLD {symbol}")

                hold.append(analysis)

            elif decision["action"] == "EXIT":

                LoggerService.warning(f"SELL {symbol}")

                exit_list.append(analysis)

                position = PortfolioService.get_position(symbol)

                if position is not None:

                    position = PositionService.normalize_position(position)
                    entry_price = float(position.get("entry_price", 0) or 0)
                    exit_price = float(analysis.get("close_price", entry_price) or entry_price)
                    quantity = float(position.get("quantity", 0) or 0)
                    cost_basis = entry_price * quantity
                    gross_profit = (exit_price - entry_price) * quantity
                    return_pct = (gross_profit / cost_basis * 100) if cost_basis else 0.0
                    highest_price = float(position.get("highest_price", entry_price) or entry_price)
                    max_profit_pct = ((highest_price - entry_price) / entry_price * 100) if entry_price else 0.0
                    max_drawdown_pct = PositionService.calculate_drawdown(position, exit_price)

                    trade = {
                        "trade_id": TradeJournalService.generate_trade_id(),
                        "symbol": symbol,
                        "entry_date": position.get("entry_date", ""),
                        "exit_date": datetime.now().strftime("%Y-%m-%d"),
                        "days_held": PositionService.calculate_days_held(position),
                        "quantity": int(quantity),
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "gross_profit": round(gross_profit, 2),
                        "return_pct": round(return_pct, 2),
                        "market_regime": regime,
                        "entry_priority": position.get("entry_priority") or analysis.get("priority") or "",
                        "entry_readiness": position.get("entry_readiness") or analysis.get("readiness_score") or 0,
                        "relative_strength": position.get("relative_strength") or analysis.get("relative_strength") or 0,
                        "exit_reason": decision.get("reason") or analysis.get("explanation") or "",
                        "max_profit_pct": round(max_profit_pct, 2),
                        "max_drawdown_pct": round(max_drawdown_pct, 2),
                    }

                    TradeJournalService.append_trade(trade)
                    LoggerService.info(f"Trade Recorded {symbol} {trade['trade_id']}")
                    PortfolioService.remove_position(symbol)

            else:

                watchlist.append(analysis)

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

            if atr is not None:
                position["current_stop"] = round(
                    highest_price - (2 * float(atr)),
                    2
                )
            elif position.get("current_stop") is not None:
                position["current_stop"] = float(position.get("current_stop"))
            elif position.get("initial_stop") is not None:
                position["current_stop"] = float(position.get("initial_stop"))
            else:
                position["current_stop"] = entry_price

        PortfolioService.save(portfolio)
        LoggerService.info("Portfolio Update")

        # ---------------------------------
        # SORT WATCHLIST
        # ---------------------------------

        watchlist = sorted(

            watchlist,

            key=lambda x: (

                x["readiness_score"],

                x["relative_strength"]

            ),

            reverse=True

        )

        full_watchlist = watchlist.copy()

        # ---------------------------------
        # BUILD REVIEW
        # ---------------------------------

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

        market_value = sum(
            float(position.get("market_value", 0) or 0)
            for position in hold
        )

        unrealized_pnl = sum(
            float(position.get("profit_amount", 0) or 0)
            for position in hold
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

        if hold:
            largest_position = max(
                hold,
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
                for position in hold
            ] + [0.0],
            default=0.0
        )

        largest_loss = min(
            [
                float(position.get("profit_amount", 0) or 0)
                for position in hold
            ] + [0.0],
            default=0.0
        )

        review = {

            "market_regime": regime,

            "buy": buy,

            "hold": hold,

            "exit": exit_list,

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

        # ---------------------------------
        # COMPARE WITH PREVIOUS REVIEW
        # ---------------------------------

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

        ReviewHistory.append(review)

        review.pop(
            "full_watchlist",
            None
        )

        return review