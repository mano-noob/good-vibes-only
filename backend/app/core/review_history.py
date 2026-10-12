import copy
import json

from runtime_paths import REVIEW_HISTORY_FILE


class ReviewHistory:

    FILE = REVIEW_HISTORY_FILE

    @staticmethod
    def load():

        if not ReviewHistory.FILE.exists():

            return []

        try:
            with ReviewHistory.FILE.open(
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

            if data is None:
                return []

            return data

        except (json.JSONDecodeError, TypeError, ValueError):
            return []

    @staticmethod
    def save(history):

        ReviewHistory.FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with ReviewHistory.FILE.open(
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                history,
                f,
                indent=4
            )

    @staticmethod
    def append(review):

        history = (
            ReviewHistory.load()
        )

        history.append(
            copy.deepcopy(review)
        )

        ReviewHistory.save(history)