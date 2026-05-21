import json
import re

from django.conf import settings
from twilio.rest import Client


def normalize_phone(phone_number, whatsapp=False):
    """
    Return a Twilio-ready phone number.

    Internal user records store numbers without '+', while Twilio expects E.164.
    WhatsApp addresses must additionally be prefixed with 'whatsapp:'.
    """
    number = re.sub(r"[^\d]", "", str(phone_number or ""))
    if not number:
        raise ValueError("Numero de telephone requis")

    e164_number = f"+{number}"
    if whatsapp:
        return f"whatsapp:{e164_number}"
    return e164_number


def _twilio_client():
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        raise ValueError("Configuration Twilio manquante: SID ou auth token")
    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def send_whatsapp(phone_number, message_text="", template_sid=None, template_variables=None, sandbox=False):
    """
    Send a WhatsApp message through Twilio.

    Production WhatsApp usually requires an approved Meta/Twilio template.
    Sandbox can still use a free-form body for manual tests.
    """
    try:
        from_number = (
            settings.TWILIO_SANDBOX_WHATSAPP_NUMBER
            if sandbox
            else settings.TWILIO_WHATSAPP_NUMBER
        )
        if not from_number:
            raise ValueError("Numero WhatsApp Twilio manquant")

        payload = {
            "from_": from_number,
            "to": normalize_phone(phone_number, whatsapp=True),
        }

        if template_sid and not sandbox:
            payload["content_sid"] = template_sid
            if template_variables:
                payload["content_variables"] = json.dumps(template_variables)
        else:
            payload["body"] = message_text

        message = _twilio_client().messages.create(**payload)
        return {"success": True, "sid": message.sid}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def send_sms(phone_number, message_text):
    """Send a classic SMS through Twilio."""
    try:
        to_number = normalize_phone(phone_number)
        from_number = getattr(settings, "TWILIO_ALPHA_SENDER_ID", None)
        if not from_number:
            from_number = settings.TWILIO_SMS_NUMBER
        if not from_number:
            raise ValueError("Numero SMS Twilio manquant")

        message = _twilio_client().messages.create(
            from_=from_number,
            to=to_number,
            body=message_text,
        )
        return {"success": True, "sid": message.sid}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def send_otp(phone_number, code, sandbox=False):
    """Send an OTP by SMS first, then fallback to WhatsApp."""
    sms_text = f"Votre code Niplan Market est {code}. Expire dans 10 minutes."

    sms = send_sms(phone_number, sms_text)
    if sms.get("success") and sms.get("sid"):
        return {"success": True, "channel": "sms", "sid": sms["sid"]}

    whatsapp = send_whatsapp(
        phone_number,
        message_text=f"Votre code Niplan Market est : {code}",
        template_sid=settings.TWILIO_OTP_TEMPLATE_SID if not sandbox else None,
        template_variables={"1": str(code)},
        sandbox=sandbox,
    )
    if whatsapp.get("success") and whatsapp.get("sid"):
        return {
            "success": True,
            "channel": "whatsapp",
            "sid": whatsapp["sid"],
            "fallback_from": "sms",
            "sms_error": sms.get("error"),
        }

    return {
        "success": False,
        "error": {
            "sms": sms.get("error"),
            "whatsapp": whatsapp.get("error"),
        },
    }


def send_welcome(phone_number, sandbox=False):
    text = (
        "Bienvenue sur Niplan Market!\n\n"
        "Votre compte est actif.\n"
        "Vous pouvez maintenant publier vos produits et recevoir des commandes."
    )

    sms = send_sms(phone_number, "Bienvenue sur Niplan Market! Votre compte est actif.")
    if sms.get("success") and sms.get("sid"):
        return {"success": True, "channel": "sms", "sid": sms["sid"]}

    whatsapp = send_whatsapp(phone_number, message_text=text, sandbox=sandbox)
    if whatsapp.get("success") and whatsapp.get("sid"):
        return {
            "success": True,
            "channel": "whatsapp",
            "sid": whatsapp["sid"],
            "fallback_from": "sms",
            "sms_error": sms.get("error"),
        }

    return {
        "success": False,
        "error": {
            "sms": sms.get("error"),
            "whatsapp": whatsapp.get("error"),
        },
    }
