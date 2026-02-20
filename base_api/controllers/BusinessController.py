from rest_framework import generics, permissions
from base_api.models import Product, Business
from base_api.serializers import BusinessSerializer

class BusinessDetailView(generics.RetrieveAPIView):
    queryset = Business.objects.all()
    serializer_class = BusinessSerializer
    lookup_field = 'slug' # Pour chercher par /maman-claire/ au lieu de l'ID
    permission_classes = [permissions.AllowAny]


class MyBusinessUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = BusinessSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.business
    
