from django.conf import settings
from rest_framework import generics, permissions
from rest_framework.response import Response
from base_api.models import Product
from base_api.serializers import ProductSerializer
from django.core.cache import cache
from rest_framework.exceptions import ValidationError

# 1. Liste de tous les produits (Public - Home Page)
class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Product.objects.filter(is_available=True).order_by('-updated_at')

        currency = self.request.query_params.get("currency")
        if currency:
            qs = qs.filter(currency=currency)

        return qs

    def list(self, request, *args, **kwargs):
        currency = request.query_params.get("currency", "all")
        page = request.query_params.get("page", "1")

        cache_key = f"product_list:{currency}:page:{page}"
        ttl = getattr(settings, "CACHE_TTL", 300)

        data = cache.get(cache_key)
        if data:
            return Response(data)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, ttl)

        return response

# 2. CRUD Produits pour le vendeur (Privé - Dashboard)

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

class MyProductEditView(generics.UpdateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug' # Pour chercher par /maman-claire/ au lieu de l'ID

    def get_queryset(self):
        return Product.objects.filter(business=self.request.user.business)

class MyProductDeleteView(generics.DestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug' # Pour chercher par /maman-claire/ au lieu de l'ID

    def get_queryset(self):
        return Product.objects.filter(business=self.request.user.business)
 
