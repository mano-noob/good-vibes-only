import json
import os


class PortfolioService:

    PORTFOLIO_FILE = "portfolio.json"

    @staticmethod
    def load():

        if not os.path.exists(
            PortfolioService.PORTFOLIO_FILE
        ):

            return {
                "cash": 100000,
                "positions": []
            }

        with open(
            PortfolioService.PORTFOLIO_FILE,
            "r"
        ) as f:

            return json.load(f)

    @staticmethod
    def save(portfolio):

        with open(
            PortfolioService.PORTFOLIO_FILE,
            "w"
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
    def is_owned(symbol):

        positions = (
            PortfolioService
            .get_positions()
        )

        return any(

            p["symbol"] == symbol

            for p in positions

        )

    @staticmethod
    def add_position(position):

        portfolio = (
            PortfolioService.load()
        )

        portfolio["positions"].append(
            position
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

            if p["symbol"] != symbol

        ]

        PortfolioService.save(
            portfolio
        )