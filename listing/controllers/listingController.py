from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Listing
from .serializers import ListingSerializer

class ListingListView(APIView):
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