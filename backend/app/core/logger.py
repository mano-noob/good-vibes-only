import threading
from datetime import datetime
from pathlib import Path


class LoggerService:
    LOGS_DIR = Path(__file__).resolve().parents[2] / "logs"
    _lock = threading.RLock()

    @classmethod
    def _log_path(cls):
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        return cls.LOGS_DIR / f"{today}.log"

    @classmethod
    def _write(cls, level: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{timestamp} [{level}] {message}\n"
        with cls._lock:
            with cls._log_path().open("a", encoding="utf-8") as handle:
                handle.write(line)

    @classmethod
    def info(cls, message: str):
        cls._write("INFO", message)

    @classmethod
    def warning(cls, message: str):
        cls._write("WARNING", message)

    @classmethod
    def error(cls, message: str):
        cls._write("ERROR", message)

    @classmethod
    def timing(cls, message: str, start_time=None):
        if start_time is None:
            cls._write("TIMING", message)
            return

        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        cls._write("TIMING", f"{message} executed in {elapsed_ms:.2f} ms")
