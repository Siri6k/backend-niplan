from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from analytics.serializers import AnalyticsEventCreateSerializer
from analytics.services import create_analytics_event, get_vendor_analytics_summary
from base_api.models import Business
from listing.models import Listing


class AnalyticsEventCreateView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = AnalyticsEventCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        listing = None
        business = None

        listing_slug = data.get("listing_slug")
        if listing_slug:
            listing = Listing.objects.select_related("business").filter(slug=listing_slug).first()
            if listing:
                business = listing.business

        business_slug = data.get("business_slug")
        if business_slug and business is None:
            business = Business.objects.filter(slug=business_slug).first()

        create_analytics_event(
            event_type=data["event_type"],
            source=data["source"],
            listing=listing,
            business=business,
            metadata=data.get("metadata", {}),
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return Response({"status": "accepted"}, status=201)


class VendorAnalyticsSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(get_vendor_analytics_summary(request.user))
