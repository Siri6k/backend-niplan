from rest_framework import viewsets, permissions, generics
from rest_framework.response import Response
from base_api.models import Product
from base_api.serializers import ProductSerializer
from django.core.cache import cache
from django.conf import settings

# 1. Liste de tous les produits (Public - Home Pag
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
class MyProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        # Sécurité : un vendeur ne voit que ses produits
        return Product.objects.filter(business=self.request.user.business).order_by('-id')

    def list_response(self):
        """Helper pour renvoyer la liste complète mise à jour"""
        queryset = self.get_queryset()
        data = ProductSerializer(queryset, many=True).data
        # Mise à jour du cache privé du vendeur
        cache.set(f"my_products:{self.request.user.id}", data, getattr(settings, "CACHE_TTL", 300))
        return Response(data)

    def perform_create(self, serializer):
        if not hasattr(self.request.user, "business") or not self.request.user.business:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"business": "Créez un business d'abord."})
        serializer.save(business=self.request.user.business)
        # Invalider le cache de la Home Page publique car il y a un nouveau produit
        cache.delete_pattern("product_list:*")

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        return self.list_response()

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        cache.delete_pattern("product_list:*") # Invalider le cache public
        return self.list_response()

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        cache.delete_pattern("product_list:*") # Invalider le cache public
        return self.list_response()