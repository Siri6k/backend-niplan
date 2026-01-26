from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action


from listing.models import Listing
from listing.serializers import ListingSerializer

class ListingListView(APIView):
    """
    Vue pour lister les annonces avec mise en cache Redis.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # On crée une clé unique basée sur les filtres (ex: "search_immo_gombe_500")
        cache_key = f"listings_{request.query_params.urlencode()}"
        
        # 1. Tenter de récupérer depuis Redis
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data) # Retour immédiat !

        # 2. Si pas en cache, faire la requête SQL normale
        listings = Listing.objects.filter(is_active=True)
        # ... tes filtres ici ...
        
        serializer = ListingSerializer(listings, many=True)
        data = serializer.data

        # 3. Stocker dans Redis pour les prochains utilisateurs
        cache.set(cache_key, data, timeout=60*15)

        return Response(data)
    
class ListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les Listings : CRUD complet
    Limite de création selon le type de compte de l'utilisateur.
    """
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # L'utilisateur ne voit que ses listings actifs
        return Listing.objects.filter(owner=self.request.user, is_active=True).order_by('-created_at')

    def perform_create(self, serializer):
        user_profile = getattr(self.request.user, 'userprofile', None)
        if not user_profile:
            raise serializers.ValidationError("Profil utilisateur introuvable.")

        # Compter les listings actifs
        listing_count = Listing.objects.filter(owner=self.request.user, is_active=True).count()

        # Définition des limites par type de compte
        account_limits = {
            'BASIC': 5,
            'PRO': 150,
            'PREMIUM': 1200,
        }
        limit = account_limits.get(user_profile.account_type.upper(), 5)

        if listing_count >= limit:
            raise serializers.ValidationError(
                f"Limite atteinte pour le compte {user_profile.account_type}. "
                f"Vous pouvez publier jusqu'à {limit} articles."
            )

        # Sauvegarde le listing avec l'utilisateur comme owner
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=['get'])
    def my_listings(self, request):
        """Retourne les listings actifs de l'utilisateur"""
        listings = self.get_queryset()
        serializer = self.get_serializer(listings, many=True)
        return Response(serializer.data)
