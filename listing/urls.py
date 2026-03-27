from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .controllers.listingController import ListingListView, ListingDetailView, ListingViewSet

router = DefaultRouter()
router.register(r'listings', ListingViewSet, basename='listing')

urlpatterns = [
    path('public/listings/', ListingListView.as_view(), name='public-listings'),
    path('public/listings/<slug:slug>/', ListingDetailView.as_view(), name='public-listing-detail'),
    path('', include(router.urls)),
]