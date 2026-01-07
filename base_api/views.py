import json
from random import randint
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Business, Product, OTPCode
from .serializers import UserSerializer, BusinessSerializer, ProductSerializer
import requests
import os



class RequestOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get('phone_whatsapp')
        # ... logique de création d'utilisateur ...

        code = str(randint(100000, 999999)) # Génère un vrai code aléatoire
        OTPCode.objects.update_or_create(phone_number=phone, defaults={'code': code})

        # --- ENVOI DU BOT ---
        try:
            send_whatsapp_otp(phone, code)
            return Response({"message": "Code envoyé sur WhatsApp"})
        except Exception as e:
            return Response({"error": "Erreur d'envoi"}, status=500)

class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get('phone_whatsapp')
        code = request.data.get('code')
        print("Code reçu:", code)
        try:
            otp = OTPCode.objects.get(phone_number=phone, code=code)
            user = User.objects.get(phone_whatsapp=phone)
            user.is_active = True
            user.save()
            
            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "business_slug": user.business.slug
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