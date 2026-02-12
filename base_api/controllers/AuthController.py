# Standard lib
import random

# Django
from django.conf import settings

# DRF
from rest_framework import  permissions
from rest_framework.response import Response
from rest_framework.views import APIView


# JWT
from rest_framework_simplejwt.tokens import RefreshToken


# Local apps
from base_api.tasks import send_welcome_sms_task, notify_subscribers_task
from base_api.models import User, OTPCode


class RequestOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get("phone_whatsapp")

        if not phone:
            return Response({"error": "Numéro requis"}, status=400)

        phone = phone.lstrip("+")

        # Code OTP
        code = "112331" # if settings.DEBUG else str(random.randint(100000, 999999))

        OTPCode.objects.update_or_create(
            phone_number=phone,
            defaults={"code": code}
        )

        if settings.DEBUG:
            print(f"[DEBUG] Code OTP pour {phone} : {code}")

        return Response({
            "status": "success",
            "message": "Code généré avec succès"
        })

class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get("phone_whatsapp", "").strip().lstrip("+")
        code = request.data.get("code", "").strip()

        if not phone or not code:
            return Response({"error": "Numéro et code requis"}, status=400)

        try:
            otp = OTPCode.objects.get(phone_number=phone, code=code)

            user, _ = User.objects.get_or_create(phone_whatsapp=phone)
            if not user.is_active:
                user.is_active = True
                user.save()

            role = "superadmin" if user.is_superuser else "vendor"

            send_welcome_sms_task.delay(
                phone,
                user.business.name if hasattr(user, "business") and user.business else "votre boutique"
            )

            refresh = RefreshToken.for_user(user)

            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "business_slug": getattr(user.business, "slug", None),
                "role": role,
                "message": "Authentification réussie"
            })

        except OTPCode.DoesNotExist:
            return Response({"error": "Code invalide"}, status=400)
