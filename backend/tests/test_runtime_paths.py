import json

import runtime_paths


def test_runtime_data_paths_and_defaults():
    assert runtime_paths.DATA_DIR.exists()
    assert runtime_paths.PORTFOLIO_FILE.exists()
    assert runtime_paths.REVIEW_HISTORY_FILE.exists()
    assert runtime_paths.STOCK_LIFECYCLE_FILE.exists()

    with open(runtime_paths.PORTFOLIO_FILE, "r", encoding="utf-8") as f:
        portfolio = json.load(f)
    assert portfolio == {"cash": 100000, "positions": []}

    with open(runtime_paths.REVIEW_HISTORY_FILE, "r", encoding="utf-8") as f:
        review_history = json.load(f)
    assert review_history == []

    with open(runtime_paths.STOCK_LIFECYCLE_FILE, "r", encoding="utf-8") as f:
        stock_lifecycle = json.load(f)
    assert stock_lifecycle == {}
