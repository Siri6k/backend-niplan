from django.core.cache import cache
from django.conf import settings

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action

from listing.models import Listing, UserProfile
from listing.serializers import (
    ListingDetailSerializer,
    ListingPublicSerializer,
    ListingOwnerSerializer,
    ListingCreateUpdateSerializer,
)


# ============================
# PUBLIC LIST (HOME PAGE)
# ============================
class ListingListView(APIView):
    """
    Vue pour lister les annonces publiques avec mise en cache Redis.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        cache_key = f"listings_{request.query_params.urlencode()}"
        ttl = getattr(settings, "CACHE_TTL", 900)

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        listings = Listing.objects.filter(is_active=True)

        # TODO: Filtres futurs
        # category = request.query_params.get("category")
        # if category:
        #     listings = listings.filter(category=category)

        serializer = ListingPublicSerializer(listings, many=True)
        data = serializer.data

        cache.set(cache_key, data, ttl)
        return Response(data)


# ============================
# AUTHENTICATED VIEWSET
# ============================
class ListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet Listings (Dashboard vendeur)
    - Limite par type de compte
    - Cache Redis par utilisateur
    - Invalidation auto
    """
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "slug"            # 👈 clé principale
    lookup_url_kwarg = "slug"        # 👈 paramètre dans l’URL
    CACHE_TTL = getattr(settings, "CACHE_TTL", 300)

    def get_queryset(self):
        business = getattr(self.request.user, 'business', None)
        if not business:
            return Listing.objects.none()
        return Listing.objects.filter(
            business=business
        ).order_by('-created_at')

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ListingCreateUpdateSerializer
        if self.action == "retrieve":
            return ListingDetailSerializer
        if self.action == "my_listings":
            return ListingOwnerSerializer
        return ListingPublicSerializer

    def _user_cache_key(self, user_id):
        return f"user_listings:{user_id}"

    def perform_create(self, serializer):
        user = self.request.user
        user_profile = getattr(user, 'userprofile', None)

        if not user_profile:
            user_profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    "phone_number": user.phone_whatsapp,
                    "account_type": "BASIC"
                }
            )

        listing_count = Listing.objects.filter(
            business=user.business, 
            is_active=True).count()

        account_limits = {
            'BASIC': 10,
            'PRO': 50,
            'PREMIUM': 100,
        }
        limit = account_limits.get(user_profile.account_type.upper(), 10)
        if listing_count >= limit and not user.is_superuser:
            raise serializers.ValidationError(
                f"Limite atteinte pour le compte {user_profile.account_type}. "
                f"Max autorisé: {limit} annonces."
            )

        listing = serializer.save(business=user.business)

        cache.delete(self._user_cache_key(user.id))
        return listing

    def perform_update(self, serializer):
        listing = serializer.save()
        cache.delete(self._user_cache_key(self.request.user.id))
        return listing

    def perform_destroy(self, instance):
        instance.delete()
        cache.delete(self._user_cache_key(self.request.user.id))

    @action(detail=False, methods=['get'])
    def my_listings(self, request):
        cache_key = self._user_cache_key(request.user.id)

        data = cache.get(cache_key)
        if data:
            return Response(data)

        listings = self.get_queryset()
        serializer = self.get_serializer(listings, many=True)
        data = serializer.data

        cache.set(cache_key, data, self.CACHE_TTL)
        return Response(data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        cache_key = f"user_listings_stats:{request.user.id}"

        data = cache.get(cache_key)
        if data:
            return Response(data)

        qs = self.get_queryset()
        data = {
            "total": qs.count(),
            "active": qs.filter(is_active=True).count(),
            "inactive": qs.filter(is_active=False).count(),
        }

        cache.set(cache_key, data, self.CACHE_TTL)
        return Response(data)
