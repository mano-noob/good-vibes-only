import json
from copy import deepcopy

from runtime_paths import STOCK_LIFECYCLE_FILE


class StockLifecycle:

    FILE_PATH = STOCK_LIFECYCLE_FILE

    @classmethod
    def load(cls):

        if not cls.FILE_PATH.exists():
            return {}

        try:

            with cls.FILE_PATH.open(
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)

        except (
            json.JSONDecodeError,
            OSError
        ):

            return {}

    @classmethod
    def save(cls, data):

        cls.FILE_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with cls.FILE_PATH.open(
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=2
            )

    @classmethod
    def update_stock(
        cls,
        symbol,
        review_date,
        status,
        readiness_score,
        priority,
        signal,
        decision
    ):

        data = cls.load()

        if symbol not in data:

            data[symbol] = {
                "symbol": symbol,
                "first_seen": review_date,
                "last_seen": review_date,
                "current_status": status,
                "current_readiness": readiness_score,
                "current_priority": priority,
                "highest_readiness": readiness_score,
                "lowest_readiness": readiness_score,
                "times_seen": 0,
                "events": []
            }

        stock = data[symbol]

        previous_status = (
            stock["current_status"]
        )

        previous_readiness = (
            stock["current_readiness"]
        )

        stock["last_seen"] = review_date

        stock["current_status"] = status

        stock["current_readiness"] = (
            readiness_score
        )

        stock["current_priority"] = priority

        stock["highest_readiness"] = max(
            stock["highest_readiness"],
            readiness_score
        )

        stock["lowest_readiness"] = min(
            stock["lowest_readiness"],
            readiness_score
        )

        stock["times_seen"] += 1

        event = {
            "date": review_date,
            "status": status,
            "readiness_score": readiness_score,
            "priority": priority,
            "signal": signal,
            "decision": decision
        }

        if (
            previous_status != status
            or previous_readiness != readiness_score
        ):

            stock["events"].append(event)

        data[symbol] = stock

        cls.save(data)

        return deepcopy(stock)
