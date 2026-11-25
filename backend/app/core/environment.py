from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=False)


def _path_setting(name: str, default: Path) -> Path:
    value = os.getenv(name)
    path = Path(value).expanduser() if value else default
    return path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()


def _int_setting(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


def _csv_setting(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    value = os.getenv(name)
    return tuple(item.strip() for item in value.split(",") if item.strip()) if value else default


@dataclass(frozen=True)
class BackendSettings:
    app_title: str
    app_version: str
    host: str
    port: int
    log_level: str
    log_dir: Path
    data_dir: Path
    cors_origins: tuple[str, ...]
    scheduler_enabled: bool
    telegram_bot_token: str | None
    telegram_chat_id: str | None
    telegram_api_base_url: str
    telegram_timeout_seconds: int


settings = BackendSettings(
    app_title=os.getenv("API_TITLE", "AI Trading Agent"),
    app_version=os.getenv("API_VERSION", "1.0.0"),
    host=os.getenv("API_HOST", "0.0.0.0"),
    port=_int_setting("API_PORT", 8000),
    log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    log_dir=_path_setting("LOG_DIR", PROJECT_ROOT / "logs"),
    data_dir=_path_setting("DATA_DIR", PROJECT_ROOT / "data"),
    cors_origins=_csv_setting(
        "CORS_ORIGINS",
        (
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ),
    ),
    scheduler_enabled=os.getenv("SCHEDULER_ENABLED", "true").strip().lower()
    not in {"0", "false", "no", "off"},
    telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN") or None,
    telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID") or None,
    telegram_api_base_url=os.getenv(
        "TELEGRAM_API_BASE_URL", "https://api.telegram.org"
    ).rstrip("/"),
    telegram_timeout_seconds=_int_setting("TELEGRAM_TIMEOUT_SECONDS", 10),
)