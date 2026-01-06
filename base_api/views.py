from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Business, Product, OTPCode
from .serializers import UserSerializer, BusinessSerializer, ProductSerializer

class RequestOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get('phone_whatsapp')
        if not phone:
            return Response({"error": "Numéro requis"}, status=400)
        
        # On crée ou récupère l'user (is_active=False par défaut)
        user, created = User.objects.get_or_create(phone_whatsapp=phone)
        
        # Génération d'un code (ici fixe '1234' pour le mode gratuit)
        code = "1234" 
        OTPCode.objects.update_or_create(phone_number=phone, defaults={'code': code})
        
        return Response({"message": "Code généré", "code_debug": code})

class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get('phone_whatsapp')
        code = request.data.get('code')
        
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
class MyProductCreateView(generics.CreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # On attache automatiquement le produit au business de l'user connecté
        serializer.save(business=self.request.user.business)

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
class MyBusinessUpdateView(generics.UpdateAPIView):
    serializer_class = BusinessSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.business