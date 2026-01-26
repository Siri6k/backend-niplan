from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .controllers.listingController import ListingListView, ListingViewSet

router = DefaultRouter()
router.register(r'listings', ListingViewSet, basename='listing')

urlpatterns = [
    path('public/listings/', ListingListView.as_view(), name='public-listings'),
    path('', include(router.urls)),
]