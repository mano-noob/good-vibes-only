"""Telegram alert delivery support."""

import requests

from app.core.environment import settings


class TelegramService:
    """Send simple Telegram text messages when credentials are configured."""

    BOT_TOKEN = settings.telegram_bot_token
    CHAT_ID = settings.telegram_chat_id
    API_BASE_URL = settings.telegram_api_base_url
    API_TIMEOUT_SECONDS = settings.telegram_timeout_seconds

    @staticmethod
    def send_message(message: str) -> dict:
        if not TelegramService.BOT_TOKEN or not TelegramService.CHAT_ID:
            return {"ok": False, "error": "Telegram credentials not configured"}

        url = (
            f"{TelegramService.API_BASE_URL}/bot"
            f"{TelegramService.BOT_TOKEN}/sendMessage"
        )
        payload = {"chat_id": TelegramService.CHAT_ID, "text": message}
        response = requests.post(url, json=payload, timeout=TelegramService.API_TIMEOUT_SECONDS)
        return response.json()