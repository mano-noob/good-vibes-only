import json

import runtime_paths


def test_runtime_data_paths_and_defaults(tmp_path, monkeypatch):
    project_root = tmp_path / "backend"
    data_dir = project_root / "data"
    monkeypatch.setattr(runtime_paths, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(runtime_paths, "DATA_DIR", data_dir)
    monkeypatch.setattr(runtime_paths, "PORTFOLIO_FILE", data_dir / "portfolio.json")
    monkeypatch.setattr(runtime_paths, "REVIEW_HISTORY_FILE", data_dir / "review_history.json")
    monkeypatch.setattr(runtime_paths, "STOCK_LIFECYCLE_FILE", data_dir / "stock_lifecycle.json")
    monkeypatch.setattr(runtime_paths, "SETTINGS_FILE", data_dir / "settings.json")

    runtime_paths.ensure_runtime_data_files()

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
