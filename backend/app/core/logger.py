import json
import logging
import threading
from datetime import datetime
from pathlib import Path


class LoggerService:
    LOGS_DIR = Path(__file__).resolve().parents[2] / "logs"
    _lock = threading.RLock()
    _logger = None

    @classmethod
    def _configure_logger(cls):
        if cls._logger is not None:
            return cls._logger

        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)

        logger = logging.getLogger("trading_agent")
        logger.setLevel(logging.INFO)
        logger.propagate = False

        if not logger.handlers:
            today = datetime.now().strftime("%Y-%m-%d")
            handler = logging.FileHandler(cls.LOGS_DIR / f"{today}.log", encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            logger.addHandler(handler)

        cls._logger = logger
        return logger

    @classmethod
    def _write(cls, level: str, message: str):
        logger = cls._configure_logger()
        with cls._lock:
            logger.log(getattr(logging, level.upper(), logging.INFO), message)

    @classmethod
    def log_event(cls, event: str, level: str = "INFO", **context):
        payload = {"event": event, **context}
        message = json.dumps(payload, default=str, sort_keys=True)
        cls._write(level, message)

    @classmethod
    def info(cls, message: str):
        cls._write("INFO", message)

    @classmethod
    def info_event(cls, event: str, **context):
        cls.log_event(event, level="INFO", **context)

    @classmethod
    def warning(cls, message: str):
        cls._write("WARNING", message)

    @classmethod
    def warning_event(cls, event: str, **context):
        cls.log_event(event, level="WARNING", **context)

    @classmethod
    def error(cls, message: str):
        cls._write("ERROR", message)

    @classmethod
    def error_event(cls, event: str, **context):
        cls.log_event(event, level="ERROR", **context)

    @classmethod
    def timing(cls, message: str, start_time=None):
        if start_time is None:
            cls._write("INFO", message)
            return

        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        cls._write("INFO", f"{message} executed in {elapsed_ms:.2f} ms")
