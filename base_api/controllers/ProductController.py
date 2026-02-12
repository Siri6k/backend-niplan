# Standard lib
import json
import os
import random

# Django
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import get_user_model

# DRF
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.exceptions import ValidationError


# JWT
from rest_framework_simplejwt.tokens import RefreshToken

# HTTP
import requests

# Local apps
from base_api.tasks import send_welcome_sms_task, notify_subscribers_task
from base_api.models import User, Business, Product, OTPCode
from base_api.serializers import UserSerializer, BusinessSerializer, ProductSerializer


# Controller pour la gestion des produits

# 1. Liste des produits disponibles avec filtrage par devise et mise en cache
class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Product.objects.filter(is_available=True).order_by("-updated_at")

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
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "slug"

    CACHE_TTL = getattr(settings, "CACHE_TTL", 300)

    def get_queryset(self):
        return Product.objects.filter(
            business=self.request.user.business
        ).order_by("-created_at")

    def perform_create(self, serializer):
        user = self.request.user

        if not hasattr(user, "business") or not user.business:
            raise ValidationError(
                {"business": "Vous devez créer un business avant d’ajouter un produit."}
            )

        product = serializer.save(business=user.business)

        # Invalide le cache
        cache.delete(f"user_products:{user.id}")
        return product

    def perform_update(self, serializer):
        product = serializer.save()
        cache.delete(f"user_products:{self.request.user.id}")
        return product

    def perform_destroy(self, instance):
        instance.delete()
        cache.delete(f"user_products:{self.request.user.id}")

    @action(detail=False, methods=["get"])
    def mine(self, request):
        """
        GET /products/mine/
        """
        cache_key = f"user_products:{request.user.id}"

        data = cache.get(cache_key)
        if data:
            return Response(data)

        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        data = serializer.data

        cache.set(cache_key, data, self.CACHE_TTL)
        return Response(data)
