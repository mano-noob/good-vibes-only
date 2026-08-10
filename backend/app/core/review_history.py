import json
import os


class ReviewHistory:

    FILE = "review_history.json"

    @staticmethod
    def load():

        if not os.path.exists(
            ReviewHistory.FILE
        ):

            return []

        with open(
            ReviewHistory.FILE,
            "r"
        ) as f:

            return json.load(f)

    @staticmethod
    def save(history):

        with open(
            ReviewHistory.FILE,
            "w"
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

        history.append(review)

        ReviewHistory.save(history)