from fastapi import APIRouter

from app.services.trading_service import TradingService
from app.services.telegram_service import TelegramService
from app.utils.alert_formatter import format_trade_alert

router = APIRouter()


@router.get("/send/{symbol}")
def send_alert(symbol: str):

    result = TradingService.analyze_stock(symbol)

    signal = result["signal"]["signal"]

    # Only send BUY alerts
    if signal != "BUY":

        return {
            "message": "No BUY signal detected.",
            "analysis": result
        }

    message = format_trade_alert(result)

    telegram_response = TelegramService.send_message(message)

    return {
        "message": "BUY alert sent successfully.",
        "analysis": result,
        "telegram_response": telegram_response
    }