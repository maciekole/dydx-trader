import requests

from src.constants import TELEGRAM_API_KEY, TELEGRAM_CHAT_ID


def send_message(message):
    url = (
        f"https://api.telegram.org/bot{TELEGRAM_API_KEY}/sendMessage"
        f"?chat_id={TELEGRAM_CHAT_ID}&text={message}"
    )
    res = requests.get(url, timeout=10)
    if res.status_code == 200:
        return "sent"
    return "failed"
