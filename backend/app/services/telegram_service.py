import os
import requests

from dotenv import load_dotenv

load_dotenv()


class TelegramService:

    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    @staticmethod
    def send_message(message: str):

        url = (
            f"https://api.telegram.org/bot"
            f"{TelegramService.BOT_TOKEN}/sendMessage"
        )

        payload = {
            "chat_id": TelegramService.CHAT_ID,
            "text": message
        }

        response = requests.post(
            url,
            json=payload
        )

        return response.json()