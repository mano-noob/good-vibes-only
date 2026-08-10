from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.alert_state import LAST_SIGNALS
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

    print("=== SCHEDULER TRIGGERED ===")

    if not is_market_open():

        print("Market closed. Skipping scan.")

        return

    print("Running automated market scan...")

    results = ScannerService.scan_market()

    for result in results:

        print(result)

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

            print(f"Duplicate alert skipped for {symbol}")

            continue

        message = format_trade_alert(result)

        TelegramService.send_message(message)

        LAST_SIGNALS[symbol] = signal

        print(f"BUY alert sent for {symbol}")


def start_scheduler():

    scheduler.add_job(
        run_market_scan,
        trigger="interval",
        minutes=15
    )

    scheduler.start()

    print(
        f"=== SCHEDULER TRIGGERED === "
        f"{datetime.now()}"
    )