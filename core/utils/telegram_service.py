import requests
from django.conf import settings

def send_otp_to_admin(phone_number, code):
    message_text = f"🔐 Code OTP pour {phone_number} : {code}"

    keyboard = {
        "inline_keyboard": [[
            {
                "text": "Envoyer au user",
                "callback_data": f"{phone_number}:{code}:sms"
            },
            {
                "text": "Envoyer WhatsApp",
                "callback_data": f"{phone_number}:{code}:whatsapp"
            }
        ]]
    }

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": settings.TELEGRAM_ADMIN_CHAT_ID,
        "text": message_text,
        "reply_markup": keyboard
    })
    return resp.json()
