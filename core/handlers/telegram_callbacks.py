# handlers/telegram_callbacks.py
import json
import logging
from django.core.cache import cache
from core.utils.telegram_service import update_otp_message
from core.utils.twilio_service import send_whatsapp, send_sms

logger = logging.getLogger(__name__)

def handle_telegram_callback(update_data):
    """
    Gère les clics sur les boutons du message Telegram
    """
    try:
        callback = json.loads(update_data["callback_query"]["data"])
        message_id = update_data["callback_query"]["message"]["message_id"]
        chat_id = update_data["callback_query"]["message"]["chat"]["id"]
        
        action = callback.get("action")
        request_id = callback.get("req_id")
        
        # Récupère les données du cache
        otp_data = cache.get(f"otp_request_{request_id}") if request_id else None
        
        if action == "send_sms":
            if otp_data:
                result = send_sms(otp_data["phone"], f"Votre code Niplan: {otp_data['code']}")
                update_otp_message(message_id, "sent_sms", f"SMS → {otp_data['phone']}")
                return {"text": "✅ SMS envoyé !"}
            
        elif action == "send_wa":
            if otp_data:
                result = send_whatsapp(otp_data["phone"], otp_data["code"])
                update_otp_message(message_id, "sent_wa", f"WhatsApp → {otp_data['phone']}")
                return {"text": "✅ WhatsApp envoyé !"}
            
        elif action == "mark_sent":
            update_otp_message(message_id, "sent_sms", "Manuellement confirmé")
            return {"text": "✅ Marqué comme envoyé"}
            
        elif action == "block":
            phone = callback.get("phone")
            # Ajoute à liste noire
            from base_api.models import BlockedNumber
            BlockedNumber.objects.get_or_create(phone=phone, reason="Admin block")
            update_otp_message(message_id, "blocked", f"Numéro: {phone}")
            return {"text": f"🚫 {phone} bloqué"}
            
        elif action == "delete":
            # Supprime le message
            delete_telegram_message(chat_id, message_id)
            return {"text": "Message supprimé"}
            
    except json.JSONDecodeError:
        logger.error("Callback data invalide")
        return {"text": "Erreur: données invalides"}
    except Exception as e:
        logger.error(f"Erreur callback: {e}")
        return {"text": f"Erreur: {str(e)}"}


def delete_telegram_message(chat_id, message_id):
    """Supprime un message Telegram"""
    import requests
    from django.conf import settings
    
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/deleteMessage"
    requests.post(url, json={"chat_id": chat_id, "message_id": message_id})