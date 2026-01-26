from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .controllers.listingController import ListingListView, ListingViewSet

router = DefaultRouter()
router.register(r'listings', ListingViewSet, basename='listing')

urlpatterns = [
    path('', ListingListView.as_view(), name='listing-list'),
    path('my-listings/', include(router.urls)),
]