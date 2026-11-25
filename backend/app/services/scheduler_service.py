from datetime import datetime
import errno
import logging
import os
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED

from app.core.alert_state import LAST_SIGNALS
from app.core.logger import LoggerService
from app.core.environment import settings
from app.services.review_service import ReviewService
from app.services.scanner_service import ScannerService
from app.services.telegram_service import TelegramService
from app.utils.alert_formatter import format_trade_alert


scheduler = BackgroundScheduler()
_scheduler_lock = threading.RLock()
_scheduler_lock_handle = None


def _acquire_process_lock() -> bool:
    global _scheduler_lock_handle

    settings.data_dir.mkdir(parents=True, exist_ok=True)
    lock_handle = open(settings.data_dir / "scheduler.lock", "a+b")
    lock_handle.seek(0, os.SEEK_END)
    if lock_handle.tell() == 0:
        lock_handle.write(b"0")
        lock_handle.flush()
    lock_handle.seek(0)

    try:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(lock_handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        lock_handle.close()
        if exc.errno in {errno.EACCES, errno.EAGAIN, errno.EDEADLK, 13, 36}:
            return False
        raise

    _scheduler_lock_handle = lock_handle
    return True


def _release_process_lock() -> None:
    global _scheduler_lock_handle

    if _scheduler_lock_handle is None:
        return

    if os.name == "nt":
        import msvcrt

        _scheduler_lock_handle.seek(0)
        msvcrt.locking(_scheduler_lock_handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        fcntl.flock(_scheduler_lock_handle.fileno(), fcntl.LOCK_UN)
    _scheduler_lock_handle.close()
    _scheduler_lock_handle = None


def _log_scheduler_event(event) -> None:
    if event.code == EVENT_JOB_ERROR:
        LoggerService.error_event(
            "scheduler_job_failed",
            job_id=event.job_id,
            exception_type=type(event.exception).__name__ if event.exception else "Unknown",
        )
    elif event.code == EVENT_JOB_MISSED:
        LoggerService.warning_event("scheduler_job_missed", job_id=event.job_id)


scheduler.add_listener(_log_scheduler_event, EVENT_JOB_ERROR | EVENT_JOB_MISSED)


def is_market_open():

    now = datetime.now()

    # Monday = 0, Sunday = 6
    weekday = now.weekday()

    # Skip weekends
    if weekday >= 5:
        return False

    current_time = now.time()

    market_open = current_time.hour > 9 or (
        current_time.hour == 9 and current_time.minute >= 15
    )

    market_close = current_time.hour < 15 or (
        current_time.hour == 15 and current_time.minute <= 30
    )

    return market_open and market_close


def run_market_scan():

    LoggerService.info_event("scheduler_execution", phase="triggered")

    if not is_market_open():

        LoggerService.info_event("scheduler_execution", phase="skipped", reason="market_closed")
        return

    LoggerService.info_event("scheduler_execution", phase="scan_started")

    results = ScannerService.scan_market()

    for result in results:

        LoggerService.info_event(
            "scanner_result",
            symbol=result.get("symbol"),
            signal=(result.get("signal") or {}).get("signal"),
        )

        if "signal" not in result:
            continue

        symbol = result["symbol"]

        signal = result["signal"]["signal"]

        # Only BUY alerts
        if signal != "BUY":
            continue

        # Avoid duplicate alerts
        previous_signal = LAST_SIGNALS.get(symbol)

        if previous_signal == signal:

            LoggerService.warning_event("duplicate_alert", symbol=symbol, signal=signal)
            continue

        message = format_trade_alert(result)

        TelegramService.send_message(message)

        LAST_SIGNALS[symbol] = signal

        LoggerService.info_event("buy_alert_sent", symbol=symbol, signal=signal)


def run_review_generation():
    LoggerService.info_event("scheduler_execution", phase="review_started")
    review = ReviewService.generate_review()
    LoggerService.info_event(
        "scheduler_execution",
        phase="review_completed",
        market_regime=review.get("market_regime"),
        buy_count=len(review.get("buy", [])),
        hold_count=len(review.get("hold", [])),
        watchlist_count=len(review.get("watchlist", [])),
    )
    return review


def start_scheduler():
    if not settings.scheduler_enabled:
        LoggerService.info_event("scheduler_disabled")
        return False

    with _scheduler_lock:
        if scheduler.running:
            return True

        if not _acquire_process_lock():
            LoggerService.warning_event("scheduler_already_owned_by_another_process")
            return False

        try:
            scheduler.add_job(
                run_market_scan,
                trigger="interval",
                minutes=15,
                id="market_scan",
                replace_existing=True,
                max_instances=1,
            )
            scheduler.add_job(
                run_review_generation,
                trigger="interval",
                minutes=15,
                id="review_generation",
                replace_existing=True,
                max_instances=1,
            )
            scheduler.start()
        except Exception:
            _release_process_lock()
            logging.getLogger("trading_agent").exception("Scheduler startup failed")
            raise

        LoggerService.info_event("scheduler_started", timestamp=datetime.now().isoformat())
        return True


def shutdown_scheduler() -> None:
    with _scheduler_lock:
        try:
            if scheduler.running:
                scheduler.shutdown(wait=True)
                LoggerService.info_event("scheduler_stopped")
        finally:
            _release_process_lock()