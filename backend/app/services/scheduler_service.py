from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.alert_state import LAST_SIGNALS
from app.core.logger import LoggerService
from app.services.review_service import ReviewService
from app.services.scanner_service import ScannerService
from app.services.telegram_service import TelegramService
from app.utils.alert_formatter import format_trade_alert


scheduler = BackgroundScheduler()


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

        LoggerService.info_event("scanner_result", symbol=result.get("symbol"), payload=result)

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

    scheduler.add_job(
        run_market_scan,
        trigger="interval",
        minutes=15
    )

    scheduler.add_job(
        run_review_generation,
        trigger="interval",
        minutes=15
    )

    scheduler.start()

    LoggerService.info_event("scheduler_started", timestamp=datetime.now().isoformat())