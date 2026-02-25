# views.py
from django.core.cache import cache
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.conf import settings
import random
import secrets

from core.utils.telegram_service import (
    send_error_to_admin, 
    send_otp_to_admin
    )
from core.utils.twilio_service import send_otp
from base_api.serializers import (
    RequestOTPSerializer, 
    VerifyOTPSerializer,
    SetPasswordSerializer,
    LoginSerializer
)
from base_api.models import User, OTPCode
from base_api.tasks import send_error_message, send_welcome_sms_task


# ============================================================================
# UTILITAIRES
# ============================================================================

def generate_otp_code():
    """Génère un code OTP sécurisé de 6 chiffres"""
    return ''.join(str(secrets.randbelow(10)) for _ in range(6))


def normalize_phone(phone):
    """Normalise le numéro de téléphone"""
    if not phone:
        return None
    phone = phone.strip()
    if phone.startswith('+'):
        phone = phone[1:]
    return phone


def get_user_role(user):
    """Détermine le rôle de l'utilisateur"""
    if user.is_superuser:
        return "superadmin"
    return "vendor"


# ============================================================================
# DÉTECTION DE FLOW (Endpoint initial recommandé)
# ============================================================================

class DetectUserFlowView(generics.GenericAPIView):
    """
    Endpoint intelligent qui détecte si l'utilisateur est :
    - Ancien (existe, doit définir MDP)
    - Existant complet (peut logger avec MDP)
    - Nouveau (besoin d'OTP)
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = RequestOTPSerializer
    
    def post(self, request):
        phone = normalize_phone(request.data.get('phone_whatsapp'))
        
        if not phone:
            return Response(
                {"error": "Numéro requis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(phone_whatsapp=phone)
            
            if user.password_setup_required:
                # Ancien utilisateur - doit définir MDP (pas besoin d'OTP)
                return Response({
                    "flow": "legacy_setup",
                    "message": "Définissez votre mot de passe pour sécuriser votre compte",
                    "requires_otp": False,
                    "next_endpoint": "/auth/legacy/set-password/",
                    "phone_whatsapp": phone
                })
            else:
                # Utilisateur complet - login avec MDP
                return Response({
                    "flow": "standard_login",
                    "message": "Connectez-vous avec votre mot de passe",
                    "requires_otp": False,
                    "next_endpoint": "/auth/login/",
                    "phone_whatsapp": phone
                })
                
        except User.DoesNotExist:
            # Nouvel utilisateur - besoin d'OTP
            return Response({
                "flow": "new_registration",
                "message": "Vérifiez votre numéro avec OTP",
                "requires_otp": True,
                "next_endpoint": "/auth/register/request-otp/",
                "phone_whatsapp": phone
            })


# ============================================================================
# POUR NOUVEAUX UTILISATEURS (Inscription avec OTP)
# ============================================================================

class NewUserRequestOTPView(generics.GenericAPIView):
    """
    Étape 1: Nouvel utilisateur - Demande d'OTP pour vérification
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = RequestOTPSerializer
    
    def post(self, request):
        phone = normalize_phone(request.data.get('phone_whatsapp'))
        
        if not phone:
            return Response(
                {"error": "Numéro requis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifie si le numéro existe déjà
        try:
            user = User.objects.get(phone_whatsapp=phone)
            
            if user.password_setup_required:
                return Response({
                    "error": "Ce numéro existe déjà. Veuillez définir votre mot de passe.",
                    "flow": "legacy_setup",
                    "redirect_to": "/api/auth/legacy/set-password/"
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    "error": "Ce numéro est déjà enregistré. Veuillez vous connecter.",
                    "flow": "standard_login",
                    "redirect_to": "/api/auth/login/"
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except User.DoesNotExist:
            pass  # Continue avec l'envoi OTP
        
        # Rate limiting
        cache_key = f"otp_attempts_{phone}"
        attempts = cache.get(cache_key, 0)
        
        if attempts >= 5:
            return Response(
                {"error": "Trop de tentatives. Réessayez dans 15 minutes."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        cache.set(cache_key, attempts + 1, timeout=900)
        
        # Génère et stocke le code
        code = generate_otp_code()
        otp_key = f"otp_{phone}"
        cache.set(otp_key, code, timeout=600)
        
        # Sauvegarde en base
        OTPCode.objects.update_or_create(
            phone_number=phone,
            defaults={'code': code}
        )
        
        # Envoi
        if settings.DEBUG:
            print(f"[DEBUG] Code OTP pour {phone} : {code}")
        
        send_otp_to_admin(phone, code)
        result = send_otp(phone, code, sandbox=True)
        
        if not result.get('success'):
            send_error_message.delay(
                f"Erreur envoi SMS à {phone}: {result.get('error')}"
            )
        
        return Response({
            "status": "success",
            "message": "Code envoyé avec succès",
            "flow": "otp_verification",
            "step": "verify_otp",
            "next_endpoint": "/api/auth/register/verify-otp/",
            "phone_whatsapp": phone
        })


class NewUserVerifyOTPView(generics.GenericAPIView):
    """
    Étape 2: Nouvel utilisateur - Vérifie OTP et crée le compte avec mot de passe
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = VerifyOTPSerializer
    
    def post(self, request):
        phone = normalize_phone(request.data.get('phone_whatsapp'))
        code = request.data.get('code', '').strip() or ""  # Permet de forcer la vérification en dev
        password = request.data.get('password')
        
        # Validations
        if not all([phone, password]):
            return Response(
                {"error": "Numéro et mot de passe requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(password) < 8:
            return Response(
                {"error": "Le mot de passe doit faire au moins 8 caractères"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifie l'OTP
        try:
            is_phone_verified = True
            if code:  # Permet de forcer la vérification en dev
                otp = OTPCode.objects.get(phone_number=phone, code=code)
            else:
                is_phone_verified = False
        except OTPCode.DoesNotExist:
            return Response(
                {"error": "Code invalide ou expiré"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crée l'utilisateur avec mot de passe
        try:
            try:
                user = User.objects.get(phone_whatsapp=phone)
                user.set_password(password)
                user.is_phone_verified = is_phone_verified
                user.password_setup_required = False
                user.is_active = True
                user.save()

            except User.DoesNotExist:
                user = User.objects.create_user(
                    phone_whatsapp=phone,
                    password=password,
                    is_phone_verified=is_phone_verified,
                    password_setup_required=False,
                    is_active=True
                )

            # Nettoyage
            if is_phone_verified:
                otp.delete()
                cache.delete(f"otp_{phone}")
            
            # Welcome SMS
            send_welcome_sms_task.delay(
                phone,
                user.business.name if hasattr(user, 'business') and user.business else "votre boutique"
            )
            
            # Tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "status": "success",
                "message": "Compte créé avec succès",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "business_slug": user.business.slug if hasattr(user, 'business') and user.business else None,
                "is_phone_verified": is_phone_verified,
                "role": get_user_role(user)
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": f"Erreur création compte: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# POUR ANCIENS UTILISATEURS (Setup mot de passe sans OTP)
# ============================================================================

class LegacyUserSetPasswordView(generics.GenericAPIView):
    """
    Ancien utilisateur: Définit son mot de passe (PAS d'OTP, déjà vérifié)
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = SetPasswordSerializer
    
    def post(self, request):
        phone = normalize_phone(request.data.get('phone_whatsapp'))
        password = request.data.get('password')
        password_confirm = request.data.get('password_confirm')
        
        # Validations
        if not all([phone, password, password_confirm]):
            return Response(
                {"error": "Tous les champs sont requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if password != password_confirm:
            return Response(
                {"error": "Les mots de passe ne correspondent pas"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(password) < 8:
            return Response(
                {"error": "Le mot de passe doit faire au moins 8 caractères"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(phone_whatsapp=phone)
            
            # Vérifie que c'est bien un ancien user
            if not user.password_setup_required:
                return Response({
                    "error": "Mot de passe déjà défini. Utilisez le login standard.",
                    "flow": "standard_login",
                    "redirect_to": "/api/auth/login/"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Définit le mot de passe
            user.set_password(password)
            user.password_setup_required = False
            user.is_active = True
            user.save()
            
            # Tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "status": "success",
                "message": "Mot de passe défini avec succès",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "is_phone_verified": user.is_phone_verified,
                "business_slug": user.business.slug if hasattr(user, 'business') and user.business else None,
                "role": get_user_role(user)
            })
            
        except User.DoesNotExist:
            return Response({
                "error": "Utilisateur non trouvé. Veuillez vous inscrire.",
                "flow": "new_registration",
                "redirect_to": "/api/auth/register/request-otp/"
            }, status=status.HTTP_404_NOT_FOUND)


# ============================================================================
# LOGIN STANDARD (Tous les users avec MDP défini)
# ============================================================================

class LoginView(generics.GenericAPIView):
    """
    Login standard: phone_whatsapp + password
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request):
        phone = normalize_phone(request.data.get('phone_whatsapp'))
        password = request.data.get('password')
        
        if not all([phone, password]):
            return Response(
                {"error": "Numéro et mot de passe requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifie d'abord si c'est un ancien user sans MDP
        try:
            user = User.objects.get(phone_whatsapp=phone)
            
            if user.password_setup_required:
                return Response({
                    "error": "Vous devez d'abord définir votre mot de passe",
                    "flow": "legacy_setup",
                    "redirect_to": "/api/auth/legacy/set-password/"
                }, status=status.HTTP_403_FORBIDDEN)
                
        except User.DoesNotExist:
            return Response(
                {"error": "Identifiants invalides"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Authentification
        user = authenticate(request, phone_whatsapp=phone, password=password)
        
        if user is None:
            return Response(
                {"error": "Identifiants invalides"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {"error": "Compte désactivé"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Génère tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            "status": "success",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "is_phone_verified": user.is_phone_verified,
            "business_slug": user.business.slug if hasattr(user, 'business') and user.business else None,
            "role": get_user_role(user)
        })


# ============================================================================
# ANCIENNES VIEWS (Conservées pour compatibilité temporaire)
# ============================================================================

class RequestOTPView(generics.GenericAPIView):
    """
    ⚠️  DEPRECATED: Utilisez /api/auth/detect-flow/ puis les endpoints spécifiques
    Conservé temporairement pour la transition
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = RequestOTPSerializer
    
    def post(self, request):
        phone = normalize_phone(request.data.get('phone_whatsapp'))
        
        if not phone:
            return Response({"error": "Numéro requis"}, status=400)
        
        # Détecte le type d'utilisateur et redirige
        try:
            user = User.objects.get(phone_whatsapp=phone) 
        except User.DoesNotExist:
            return Response(
                {"error": "Numéro non enregistré. Veuillez vous inscrire."},
                status=status.HTTP_404_NOT_FOUND
            )          
   
        # Rate limiting
        cache_key = f"otp_attempts_{phone}"
        attempts = cache.get(cache_key, 0)
        
        if attempts >= 5:
            return Response(
                {"error": "Trop de tentatives. Réessayez dans 15 minutes."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        cache.set(cache_key, attempts + 1, timeout=900)
        
        # Génère et envoie OTP
        code = generate_otp_code()
        otp_key = f"otp_{phone}"
        cache.set(otp_key, code, timeout=600)
        
        OTPCode.objects.update_or_create(
            phone_number=phone,
            defaults={'code': code}
        )
        
        if settings.DEBUG:
            print(f"[DEBUG] Code OTP pour {phone} : {code}")
        
        send_otp_to_admin(phone, code)
        result = send_otp(phone, code, sandbox=True)
        
        if not result.get('success'):
            send_error_message.delay(
                f"Erreur envoi SMS à {phone}: {result.get('error')}"
            )
        
        return Response({
            "status": "success",
            "message": "Code envoyé avec succès"
        })


class VerifyOTPView(generics.GenericAPIView):
    """
    ⚠️  DEPRECATED: Pour nouveaux users, utilisez /api/auth/register/verify-otp/
    Pour anciens, plus besoin d'OTP
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = VerifyOTPSerializer

    def post(self, request):
        phone = normalize_phone(request.data.get('phone_whatsapp'))
        code = request.data.get('otp_code', '').strip()
        
        if not all([phone, code]):
            return Response(
                {"error": "Numéro et code requis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            otp = OTPCode.objects.get(phone_number=phone, code=code)
            user = User.objects.get(phone_whatsapp=phone)
            user.is_phone_verified = True
            if not user.is_active:
                user.is_active = True
                user.save()
        except (User.DoesNotExist, OTPCode.DoesNotExist):
            return Response(
                {"error": "Code invalide"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        refresh = RefreshToken.for_user(user)
        otp.delete()
        cache.delete(f"otp_{phone}")
        
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "is_phone_verified": user.is_phone_verified,  
            "business_slug": user.business.slug if hasattr(user, 'business') and user.business else None,
            "role": get_user_role(user),
            "message": "Verification du numéro réussie"
        })