import requests
import logging
from urllib.parse import quote
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

def escape_markdown_v2(text: str) -> str:
    """
    Échappe les caractères spéciaux pour MarkdownV2 de Telegram
    """
    chars_to_escape = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for c in chars_to_escape:
        text = text.replace(c, f'\\{c}')
    return text

def send_otp_to_admin(phone_number: str, code: str, request_source="web") -> dict:
    """
    Envoie OTP à l'admin Telegram avec bouton pour envoyer SMS/WhatsApp
    """
    phone_clean = phone_number.replace("+", "").replace(" ", "")

    wa_text = f"Votre code OTP est : {code}\n Expire dans 10 minutes \n\n Niplan Market - RDC "
    wa_text_encoded = quote(wa_text)

    wa_link = f"https://wa.me/{phone_clean}?text={wa_text_encoded}"
    tg_text = f"🔐 OTP pour {phone_number}\nCode: {code}\nSource: {request_source}"
    tg_link = f"https://t.me/{phone_clean}?start=otp_{phone_clean}_{code}"   

    message_text = (
        f"🔐 *OTP UTILISATEUR*\n\n"
        f"📱 Numéro : `{phone_number}`\n"
        f"🔑 Code : `{code}`\n\n"
        f"Choisissez comment l’envoyer 👇"
    )

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "📲 WhatsApp", "url": wa_link},
                {"text": "💬 Telegram", "url": tg_link}
            ],
            [
                {"text": "❌ Supprimer", "url": "https://t.me"}
            ]
        ]
    }

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": settings.TELEGRAM_ADMIN_CHAT_ID,
        "text": message_text,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }

    response = requests.post(url, json=payload, timeout=10)
    return response.json()

def send_error_to_admin(error_message: str) -> dict:
    """
    Envoie un message d'erreur à l'admin Telegram
    """
    message_text = f"⚠️ *ERREUR OTP*\n\n{escape_markdown_v2(error_message)}"
    
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": settings.TELEGRAM_ADMIN_CHAT_ID,
        "text": message_text,
        "parse_mode": "Markdown"
    }
    
    response = requests.post(url, json=payload, timeout=10)
    return response.json()