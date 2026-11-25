from fastapi import APIRouter

from app.core.api_response import exception_response, success_response
from app.services.telegram_service import TelegramService
from app.services.trading_service import TradingService
from app.utils.alert_formatter import format_trade_alert

router = APIRouter()


@router.get("/send/{symbol}")
def send_alert(symbol: str):
    try:
        result = TradingService.analyze_stock(symbol)
        signal = result["signal"]["signal"]

        if signal != "BUY":
            return success_response({
                "message": "No BUY signal detected.",
                "analysis": result,
            })

        message = format_trade_alert(result)
        telegram_response = TelegramService.send_message(message)

        return success_response({
            "message": "BUY alert sent successfully.",
            "analysis": result,
            "telegram_response": telegram_response,
        })
    except Exception as exc:  # pragma: no cover - API error handling
        return exception_response("Failed to send alert", exc)