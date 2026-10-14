"""Telegram alert delivery support."""

import os

import requests
from dotenv import load_dotenv

load_dotenv()


class TelegramService:
    """Send simple Telegram text messages when credentials are configured."""

    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    API_TIMEOUT_SECONDS = 10

    @staticmethod
    def send_message(message: str) -> dict:
        if not TelegramService.BOT_TOKEN or not TelegramService.CHAT_ID:
            return {"ok": False, "error": "Telegram credentials not configured"}

        url = (
            f"https://api.telegram.org/bot"
            f"{TelegramService.BOT_TOKEN}/sendMessage"
        )
        payload = {"chat_id": TelegramService.CHAT_ID, "text": message}
        response = requests.post(url, json=payload, timeout=TelegramService.API_TIMEOUT_SECONDS)
        return response.json()