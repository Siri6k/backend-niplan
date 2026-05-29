from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from analytics.models import AnalyticsEvent
from listing.models import Listing


def create_analytics_event(*, event_type, source, listing=None, business=None, metadata=None, ip_address=None, user_agent=""):
    if listing and not business:
        business = listing.business

    return AnalyticsEvent.objects.create(
        event_type=event_type,
        source=source,
        listing=listing,
        business=business,
        metadata=metadata or {},
        ip_address=ip_address,
        user_agent=(user_agent or "")[:255],
    )


def get_vendor_analytics_summary(user):
    business = getattr(user, "business", None)
    if not business:
        return {
            "active_listings": 0,
            "listing_views_total": 0,
            "business_views_total": 0,
            "whatsapp_clicks_total": 0,
            "whatsapp_clicks_7d": 0,
            "contact_rate": 0,
            "top_listings": [],
        }

    whatsapp_events = AnalyticsEvent.objects.filter(
        business=business,
        event_type="whatsapp_click",
    )
    listing_views_total = AnalyticsEvent.objects.filter(
        business=business,
        event_type="listing_view",
    ).count()
    business_views_total = AnalyticsEvent.objects.filter(
        business=business,
        event_type="business_view",
    ).count()
    since_7d = timezone.now() - timedelta(days=7)
    top_listings = (
        Listing.objects.filter(business=business, is_active=True)
        .annotate(
            whatsapp_clicks=Count(
                "analytics_events",
                filter=Q(analytics_events__event_type="whatsapp_click"),
            ),
            listing_views=Count(
                "analytics_events",
                filter=Q(analytics_events__event_type="listing_view"),
            )
        )
        .filter(Q(whatsapp_clicks__gt=0) | Q(listing_views__gt=0))
        .order_by("-whatsapp_clicks", "-updated_at")[:5]
    )
    whatsapp_clicks_total = whatsapp_events.count()

    return {
        "active_listings": Listing.objects.filter(business=business, is_active=True).count(),
        "listing_views_total": listing_views_total,
        "business_views_total": business_views_total,
        "whatsapp_clicks_total": whatsapp_clicks_total,
        "whatsapp_clicks_7d": whatsapp_events.filter(created_at__gte=since_7d).count(),
        "contact_rate": round((whatsapp_clicks_total / listing_views_total) * 100, 1)
        if listing_views_total
        else 0,
        "top_listings": [
            {
                "slug": listing.slug,
                "title": listing.title,
                "listing_views": listing.listing_views,
                "whatsapp_clicks": listing.whatsapp_clicks,
            }
            for listing in top_listings
        ],
    }
