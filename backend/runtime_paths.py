import json
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
PORTFOLIO_FILE = DATA_DIR / "portfolio.json"
REVIEW_HISTORY_FILE = DATA_DIR / "review_history.json"
STOCK_LIFECYCLE_FILE = DATA_DIR / "stock_lifecycle.json"


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=4)


def _ensure_default_file(path: Path, payload):
    if path.exists():
        return
    _write_json(path, payload)


def _migrate_legacy_file(legacy_path: Path, target_path: Path):
    if target_path.exists() or not legacy_path.exists():
        return
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(legacy_path, target_path)


def ensure_runtime_data_files():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    _migrate_legacy_file(PROJECT_ROOT / "portfolio.json", PORTFOLIO_FILE)
    _migrate_legacy_file(PROJECT_ROOT / "review_history.json", REVIEW_HISTORY_FILE)
    _migrate_legacy_file(PROJECT_ROOT / "stock_lifecycle.json", STOCK_LIFECYCLE_FILE)

    _ensure_default_file(PORTFOLIO_FILE, {"cash": 100000, "positions": []})
    _ensure_default_file(REVIEW_HISTORY_FILE, [])
    _ensure_default_file(STOCK_LIFECYCLE_FILE, {})


ensure_runtime_data_files()
