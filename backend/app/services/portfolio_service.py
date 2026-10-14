"""Portfolio persistence and mutation helpers."""

import json

from app.core.config_service import ConfigService
from app.core.logger import LoggerService
from app.services.position_service import PositionService
from runtime_paths import PORTFOLIO_FILE


class PortfolioService:
    """Load, normalize, and save the runtime portfolio record."""

    PORTFOLIO_FILE = PORTFOLIO_FILE

    @staticmethod
    def load():

        if not PortfolioService.PORTFOLIO_FILE.exists():

            LoggerService.info_event("portfolio_loaded", source="default")
            return {
                "cash": ConfigService.get("capital", 100000),
                "positions": []
            }

        with PortfolioService.PORTFOLIO_FILE.open(
            "r",
            encoding="utf-8"
        ) as f:

            portfolio = json.load(f)

        if portfolio is None:
            return {
                "cash": ConfigService.get("capital", 100000),
                "positions": []
            }

        portfolio.setdefault("cash", ConfigService.get("capital", 100000))
        portfolio.setdefault("positions", [])

        LoggerService.info_event("portfolio_loaded", positions=len(portfolio.get("positions", [])), cash=portfolio.get("cash"))

        portfolio["positions"] = [
            PositionService.normalize_position(position)
            for position in portfolio["positions"]
        ]

        return portfolio

    @staticmethod
    def save(portfolio):

        LoggerService.info_event("portfolio_saved", positions=len(portfolio.get("positions", [])), cash=portfolio.get("cash"))

        PortfolioService.PORTFOLIO_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with PortfolioService.PORTFOLIO_FILE.open(
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                portfolio,
                f,
                indent=4
            )

    @staticmethod
    def get_positions():

        portfolio = (
            PortfolioService.load()
        )

        return portfolio.get(
            "positions",
            []
        )

    @staticmethod
    def get_position(symbol):

        positions = (
            PortfolioService
            .get_positions()
        )

        for position in positions:

            if position.get("symbol") == symbol:

                return position

        return None

    @staticmethod
    def is_owned(symbol):

        return (
            PortfolioService
            .get_position(symbol)
            is not None
        )

    @staticmethod
    def add_position(position):

        portfolio = (
            PortfolioService.load()
        )

        normalized_position = PositionService.normalize_position(position)

        symbol = normalized_position.get("symbol")

        existing = next(
            (
                p
                for p in portfolio["positions"]
                if p.get("symbol") == symbol
            ),
            None
        )

        if existing:

            raise ValueError(
                f"Position already exists: {symbol}"
            )

        normalized_position.setdefault("highest_price", normalized_position.get("entry_price", 0.0))
        normalized_position.setdefault("highest_profit_pct", 0.0)
        normalized_position.setdefault("max_drawdown_pct", 0.0)
        normalized_position.setdefault("current_stop", normalized_position.get("initial_stop", 0.0))
        normalized_position.setdefault("entry_priority", "")
        normalized_position.setdefault("entry_readiness", 0)
        normalized_position.setdefault("relative_strength", 0.0)
        normalized_position.setdefault("market_regime", "")
        normalized_position.setdefault("entry_signal", "")
        normalized_position.setdefault("entry_date", normalized_position.get("entry_date") or "")

        portfolio["positions"].append(
            normalized_position
        )

        PortfolioService.save(
            portfolio
        )

    @staticmethod
    def remove_position(symbol):

        portfolio = (
            PortfolioService.load()
        )

        portfolio["positions"] = [

            p

            for p in portfolio["positions"]

            if p.get("symbol") != symbol

        ]

        PortfolioService.save(
            portfolio
        )