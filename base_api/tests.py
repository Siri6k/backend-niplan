from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from core.utils.twilio_service import normalize_phone, send_otp, send_welcome


class TwilioServiceTests(SimpleTestCase):
    def test_normalize_phone_for_sms_and_whatsapp(self):
        self.assertEqual(normalize_phone("+243 899-530-506"), "+243899530506")
        self.assertEqual(
            normalize_phone("243899530506", whatsapp=True),
            "whatsapp:+243899530506",
        )

    @override_settings(
        TWILIO_ACCOUNT_SID="AC_test",
        TWILIO_AUTH_TOKEN="token",
        TWILIO_WHATSAPP_NUMBER="whatsapp:+14155238886",
        TWILIO_OTP_TEMPLATE_SID="HX_template",
        TWILIO_SMS_NUMBER="+15005550006",
        TWILIO_ALPHA_SENDER_ID=None,
    )
    @patch("core.utils.twilio_service.Client")
    def test_send_otp_uses_sms_first(self, client_class):
        client = Mock()
        client.messages.create.return_value = SimpleNamespace(sid="SM_sms")
        client_class.return_value = client

        result = send_otp("243899530506", "123456")

        self.assertEqual(result["channel"], "sms")
        client.messages.create.assert_called_once()
        payload = client.messages.create.call_args.kwargs
        self.assertEqual(payload["to"], "+243899530506")
        self.assertEqual(payload["from_"], "+15005550006")
        self.assertIn("123456", payload["body"])

    @override_settings(
        TWILIO_ACCOUNT_SID="AC_test",
        TWILIO_AUTH_TOKEN="token",
        TWILIO_WHATSAPP_NUMBER="whatsapp:+14155238886",
        TWILIO_OTP_TEMPLATE_SID="HX_template",
        TWILIO_SMS_NUMBER="+15005550006",
        TWILIO_ALPHA_SENDER_ID=None,
    )
    @patch("core.utils.twilio_service.Client")
    def test_send_otp_falls_back_to_whatsapp_when_sms_fails(self, client_class):
        client = Mock()
        client.messages.create.side_effect = [
            Exception("sms failed"),
            SimpleNamespace(sid="SM_whatsapp"),
        ]
        client_class.return_value = client

        result = send_otp("243899530506", "123456")

        self.assertTrue(result["success"])
        self.assertEqual(result["channel"], "whatsapp")
        self.assertEqual(result["fallback_from"], "sms")
        self.assertEqual(client.messages.create.call_count, 2)
        whatsapp_payload = client.messages.create.call_args.kwargs
        self.assertEqual(whatsapp_payload["to"], "whatsapp:+243899530506")
        self.assertEqual(whatsapp_payload["content_sid"], "HX_template")
        self.assertEqual(whatsapp_payload["content_variables"], '{"1": "123456"}')

    @override_settings(
        TWILIO_ACCOUNT_SID="AC_test",
        TWILIO_AUTH_TOKEN="token",
        TWILIO_WHATSAPP_NUMBER="whatsapp:+14155238886",
        TWILIO_SANDBOX_WHATSAPP_NUMBER="whatsapp:+14155238886",
        TWILIO_SMS_NUMBER="+15005550006",
        TWILIO_ALPHA_SENDER_ID=None,
    )
    @patch("core.utils.twilio_service.Client")
    def test_send_welcome_uses_sms_first(self, client_class):
        client = Mock()
        client.messages.create.return_value = SimpleNamespace(sid="SM_sms")
        client_class.return_value = client

        result = send_welcome("243899530506")

        self.assertTrue(result["success"])
        self.assertEqual(result["channel"], "sms")
        client.messages.create.assert_called_once()
        payload = client.messages.create.call_args.kwargs
        self.assertEqual(payload["to"], "+243899530506")
