from twilio.rest import Client
from django.conf import settings
import json

# 🔹 Helper pour nettoyer le numéro
def normalize_phone(phone_number, whatsapp=False):
    number = phone_number.replace('+', '').replace(' ', '')
    if whatsapp:
        return f"whatsapp:+{number}"
    return f"+{number}"

# 🔹 Fonction pour envoyer WhatsApp (Sandbox ou Prod)
def send_whatsapp(phone_number, message_text="", template_sid=None, sandbox=False):
    """
    Envoi WhatsApp via Twilio.
    sandbox=True => utilise le numéro sandbox Twilio
    template_sid => pour prod avec template (OTP, etc.)
    """
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, 
                        settings.TWILIO_AUTH_TOKEN)
        phone = "+243899530506" if sandbox else phone_number  # Override pour sandbox si besoin

        to_number = normalize_phone(phone, whatsapp=True)
        from_number = settings.TWILIO_SANDBOX_WHATSAPP_NUMBER if sandbox else settings.TWILIO_WHATSAPP_NUMBER

        kwargs = {
            "from_": from_number,
            "to": to_number
        }

        if sandbox:
            # Sandbox = message libre
            kwargs["body"] = message_text
        else:
            # Prod = template ou body
            if template_sid:
                kwargs["content_sid"] = template_sid
                kwargs["body"] = message_text  # body pour variables du template si besoin
            else:
                kwargs["body"] = message_text

        message = client.messages.create(**kwargs)

        return {"success": True, "sid": message.sid}

    except Exception as e:
        return {"success": False, "error": str(e)}

# 🔹 Fallback SMS classique
def send_sms(phone_number, message_text):
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        to_number = normalize_phone(phone_number)
        message = client.messages.create(
            from_=settings.TWILIO_SMS_NUMBER,
            to=to_number,
            body=message_text
        )
        return {"success": True, "sid": message.sid}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 🔹 OTP avec fallback WhatsApp → SMS
def send_otp(phone_number, code, sandbox=False):
    otp_text = f"🔐 Votre code Niplan Market est : {code}"
    if sandbox:
        otp_text += f"\n\n[Mode Sandbox] Ce message est envoyé depuis le numéro de test Twilio. \n Tranferez ca au numéro {normalize_phone(phone_number, whatsapp=True)} pour tester l'OTP WhatsApp."

    # 1️⃣ Essai WhatsApp
    whatsapp = send_whatsapp(
        phone_number,
        message_text=otp_text,
        template_sid=settings.TWILIO_OTP_TEMPLATE_SID if not sandbox else None,
        sandbox=sandbox
    )
    if whatsapp["success"]:
        return {"success": True, "channel": "whatsapp", "sid": whatsapp["sid"]}

    # 2️⃣ Fallback SMS
    sms = send_sms(phone_number, f"Votre code Niplan Market est {code}. Expire dans 10 minutes.")
    if sms["success"]:
        return {"success": True, "channel": "sms", "sid": sms["sid"]}

    # 3️⃣ Échec total
    return {"success": False, "error": {"whatsapp": whatsapp.get("error"), "sms": sms.get("error")}}

# 🔹 SMS de bienvenue (Sandbox ou Prod)
def send_welcome(phone_number,  sandbox=False):
    text = (
        f"Bienvenue sur Niplan Market!\n\n"
        "Votre compte est actif.\n"
        "Vous pouvez maintenant publier vos produits et recevoir des commandes."
    )

    return send_whatsapp(phone_number, message_text=text, sandbox=sandbox)
