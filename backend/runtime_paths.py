import json
import shutil
from pathlib import Path
from typing import Any

from app.core.environment import PROJECT_ROOT, settings

DATA_DIR = settings.data_dir
PORTFOLIO_FILE = DATA_DIR / "portfolio.json"
REVIEW_HISTORY_FILE = DATA_DIR / "review_history.json"
STOCK_LIFECYCLE_FILE = DATA_DIR / "stock_lifecycle.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
TRADES_FILE = DATA_DIR / "trades.json"
TRADE_HISTORY_FILE = DATA_DIR / "trade_history.json"

DEFAULT_PORTFOLIO = {"cash": 100000, "positions": []}
DEFAULT_SETTINGS: dict[str, Any] = {
    "risk_percent": 2.0,
    "watchlist_size": 10,
    "starting_cash": 100000,
    "market_filter": "Bullish",
    "auto_update_stop": True,
    "capital": 100000,
    "relative_strength_count": 20,
    "risk_per_trade_pct": 2,
    "max_positions": 8,
    "max_sector_exposure_pct": 25,
    "atr_multiplier": 2,
    "target_rr": 2.5,
    "breakout_lookback": 55,
    "volume_lookback": 20,
    "consolidation_lookback": 10,
    "consolidation_range": 0.08,
    "volume_multiplier": 1.5,
    "rsi_buy_threshold": 55,
    "ema_fast": 20,
    "ema_medium": 50,
    "ema_slow": 200,
    "relative_strength_3m_lookback": 63,
    "relative_strength_6m_lookback": 126,
    "relative_strength_12m_lookback": 252,
    "relative_strength_3m_weight": 0.3,
    "relative_strength_6m_weight": 0.3,
    "relative_strength_12m_weight": 0.4,
    "backtest_brokerage_pct": 0.03,
    "backtest_transaction_cost_pct": 0.10,
    "backtest_slippage_bps": 5.0,
    "priority": {"A": 90, "B": 75, "C": 60, "D": 40},
}


def _write_json(path: Path, payload: Any) -> None:
    """Persist JSON to disk while ensuring parent directories exist."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=4)


def _ensure_default_file(path: Path, payload: Any) -> None:
    """Create a default file only if it is missing."""
    if path.exists():
        return
    _write_json(path, payload)


def _migrate_legacy_file(legacy_path: Path, target_path: Path) -> None:
    """Migrate runtime JSON out of the old project root into the centralized data directory."""
    if target_path.exists() or not legacy_path.exists():
        return
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(legacy_path, target_path)


def ensure_runtime_data_files() -> None:
    """Ensure all runtime JSON files exist in the single project data directory."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    _migrate_legacy_file(PROJECT_ROOT / "portfolio.json", PORTFOLIO_FILE)
    _migrate_legacy_file(PROJECT_ROOT / "review_history.json", REVIEW_HISTORY_FILE)
    _migrate_legacy_file(PROJECT_ROOT / "stock_lifecycle.json", STOCK_LIFECYCLE_FILE)

    _ensure_default_file(PORTFOLIO_FILE, DEFAULT_PORTFOLIO)
    _ensure_default_file(REVIEW_HISTORY_FILE, [])
    _ensure_default_file(STOCK_LIFECYCLE_FILE, {})
    _ensure_default_file(SETTINGS_FILE, DEFAULT_SETTINGS)


ensure_runtime_data_files()

__all__ = [
    "PROJECT_ROOT",
    "DATA_DIR",
    "PORTFOLIO_FILE",
    "REVIEW_HISTORY_FILE",
    "STOCK_LIFECYCLE_FILE",
    "SETTINGS_FILE",
    "TRADES_FILE",
    "TRADE_HISTORY_FILE",
    "DEFAULT_PORTFOLIO",
    "DEFAULT_SETTINGS",
    "ensure_runtime_data_files",
]
