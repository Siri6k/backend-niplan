import json
from random import randint
from django.conf import settings
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Business, Product, OTPCode
from .serializers import UserSerializer, BusinessSerializer, ProductSerializer
import requests
import os
from rest_framework.permissions import IsAdminUser
from django.contrib.auth import get_user_model

import random # N'oublie pas l'import

class RequestOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get('phone_whatsapp')
        
        if not phone:
            return Response({"error": "Numéro requis"}, status=400)
        if phone.startswith('+'):
            phone = phone[1:]  # Enlève le '+'

        # 1. Génération du code (6 chiffres)
        #code = str(random.randint(100000, 999999)) 
        code = "112331"  # Code fixe pour les tests
        
        # 2. Sauvegarde ou mise à jour en base de données
        OTPCode.objects.update_or_create(
            phone_number=phone, 
            defaults={'code': code}
        )
        if settings.DEBUG:
            print(f"[DEBUG] Code OTP pour {phone} : {code}")

        # 3. Réponse directe avec le code (On enlève la logique WhatsApp)
        return Response({
            "status": "success",
            "message": "Code généré avec succès",
        })

class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

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
            print("Génération des tokens pour l'utilisateur:", user.phone_whatsapp)
                       
            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "business_slug": user.business.slug,
                "role": role,
                "message": "Authentification réussie"
            })
        except:
            return Response({"error": "Code invalide"}, status=400)
        


# 1. Liste de tous les produits (Public - Home Page)
class ProductListView(generics.ListAPIView):
    queryset = Product.objects.filter(is_available=True).order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

# 2. CRUD Produits pour le vendeur (Privé - Dashboard)
from rest_framework.exceptions import ValidationError

# 3. Liste privée pour le Dashboard (Uniquement les miens)
class MyProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # On filtre strictement par le business de l'utilisateur connecté
        return Product.objects.filter(business=self.request.user.business).order_by('-created_at')

class MyProductCreateView(generics.CreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user

        if not hasattr(user, "business") or not user.business:
            raise ValidationError(
                {"business": "Vous devez créer un business avant d’ajouter un produit."}
            )

        serializer.save(business=user.business)


class MyProductDeleteView(generics.DestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(business=self.request.user.business)
    

class BusinessDetailView(generics.RetrieveAPIView):
    queryset = Business.objects.all()
    serializer_class = BusinessSerializer
    lookup_field = 'slug' # Pour chercher par /maman-claire/ au lieu de l'ID
    permission_classes = [permissions.AllowAny]

# Mise à jour de sa propre boutique (Logo, Nom)
class MyBusinessUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = BusinessSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.business
    
def send_whatsapp_otp(phone_number, code):
    ultraMSGInstance = os.getenv('ULTRAMSG_INSTANCE')
    url = f"https://api.ultramsg.com/{ultraMSGInstance}/messages/chat"
    payload = json.dumps({
        "token": "{TOKEN}",
        "to": phone_number,
        "body": f"Votre code Niplan Market est : *{code}*"
    })
    headers = {'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    
    print(response.text)



class AdminUserListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        users = User.objects.all().order_by('-date_joined')
        data = [{
            "id": u.id,
            "phone": u.phone_whatsapp,
            "is_active": u.is_active,
            "date_joined": u.date_joined.strftime("%d/%m/%Y %H:%M")
        } for u in users]
        return Response(data)

class AdminOTPLogView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # On récupère les 20 derniers codes générés
        otps = OTPCode.objects.all().order_by('-id')[:20]
        data = [{
            "id": o.id,
            "phone": o.phone_number,
            "code": o.code,
            "created_at": o.created_at.strftime("%H:%M:%S") # Heure de génération
        } for o in otps]
        return Response(data)