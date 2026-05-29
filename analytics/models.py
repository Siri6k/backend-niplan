from django.db import models

from base_api.models import Business
from listing.models import Listing


class AnalyticsEvent(models.Model):
    EVENT_TYPES = [
        ("whatsapp_click", "WhatsApp click"),
        ("listing_view", "Listing view"),
        ("business_view", "Business view"),
        ("share_click", "Share click"),
    ]

    event_type = models.CharField(max_length=40, choices=EVENT_TYPES)
    source = models.CharField(max_length=80)
    business = models.ForeignKey(
        Business,
        on_delete=models.SET_NULL,
        related_name="analytics_events",
        blank=True,
        null=True,
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.SET_NULL,
        related_name="analytics_events",
        blank=True,
        null=True,
    )
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "-created_at"]),
            models.Index(fields=["business", "event_type", "-created_at"]),
            models.Index(fields=["listing", "event_type", "-created_at"]),
        ]

    def __str__(self):
        target = self.listing or self.business or "unknown"
        return f"{self.event_type} from {self.source} on {target}"
