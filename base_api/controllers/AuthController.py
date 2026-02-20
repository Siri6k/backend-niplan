from django.core.cache import cache
from rest_framework import generics, permissions
from core.utils.telegram_service import send_otp_to_admin
from core.utils.twilio_service import send_otp
from base_api.serializers import RequestOTPSerializer, VerifyOTPSerializer

from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from base_api.models import User, OTPCode
from base_api.tasks import send_welcome_sms_task
from django.conf import settings
import random # N'oublie pas l'import
import secrets # Pour une génération de code plus sécurisée
import json
from twilio.rest import Client

class RequestOTPView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RequestOTPSerializer
    
    def post(self, request):
        phone = request.data.get('phone_whatsapp')
        
        if not phone:
            return Response({"error": "Numéro requis"}, status=400)
        if phone.startswith('+'):
            phone = phone[1:]  # Enlève le '+'

        # Vérifie si pas trop de tentatives récentes
        cache_key = f"otp_attempts_{phone}"
        attempts = cache.get(cache_key, 0)
    
        if attempts >= 5:
            raise Exception("Trop de tentatives. Réessayez dans 15 minutes.")
        
        # Incrémente le compteur
        cache.set(cache_key, attempts + 1, timeout=900)  # 15 min

        # 1. Génération du code (6 chiffres)
        # code = str(random.randint(100000, 999999)) 
        #code = str(112331)  # Code fixe pour les tests
        # Génère le code
        code = ''.join(str(secrets.randbelow(10)) for _ in range(6))
        
        # Stocke dans cache avec expiration courte (10 min)
        otp_key = f"otp_{phone}"
        cache.set(otp_key, code, timeout=600)  # 10 minutes
        
        # 2. Sauvegarde ou mise à jour en base de données
        OTPCode.objects.update_or_create(
            phone_number=phone, 
            defaults={'code': code}
        )
        if settings.DEBUG:
            print(f"[DEBUG] Code OTP pour {phone} : {code}")

        # 3. Envoi du code via Twilio
        send_otp_to_admin(phone, code)  # Envoie le code au superadmin sur Telegram pour validation manuelle (sandbox)
        result = send_otp(phone, code, sandbox=True)
        print(f"Résultat de l'envoi WhatsApp: {result}")
        if not result['success']:
            return Response({
                    "error": "Erreur d'envoi WhatsApp",
                    "details": result.get('error')
                }, status=500)

        return Response({
            "status": "success",
            "message": "Code généré avec succès",
        })

class VerifyOTPView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = VerifyOTPSerializer

    def post(self, request):
        phone = request.data.get('phone_whatsapp').strip()
        code = request.data.get('code').strip()
        if not phone:
            return Response({"error": "Numéro requis"}, status=400)
        if phone.startswith('+'):
            phone = phone[1:]  # Enlève le '+'

        print("Code reçu:", code)
        try:
            print("Vérification du code pour le numéro:", phone)
            otp = OTPCode.objects.get(phone_number=phone, code=code)
            print("Code valide trouvé:", otp.code)
            user = User.objects.get_or_create(phone_whatsapp=phone)[0]
            if not user.is_active:
                user.is_active = True
                user.save()
            role="vendor"

            if user.is_superuser is True:
                role="superadmin"
            
            send_welcome_sms_task.delay(
                phone, 
                user.business.name if user.business else "votre boutique"
                )
            refresh = RefreshToken.for_user(user)
            cache.delete(f"otp_{phone}")
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "business_slug": user.business.slug if user.business else None,
                "role": role,
                "message": "Authentification réussie"
            })
        except:
            
            return Response({"error": "Code invalide"}, status=400)
        





    
