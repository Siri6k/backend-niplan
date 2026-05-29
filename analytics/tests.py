import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from analytics.models import AnalyticsEvent
from listing.models import Listing

User = get_user_model()


class AnalyticsEventModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone_whatsapp="243899530506",
            password="testpassword123",
        )
        self.business = self.user.business
        self.business.name = "Boutique Test"
        self.business.business_type = "SHOP"
        self.business.save()
        self.listing = Listing.objects.create(
            business=self.business,
            title="iPhone 13 Pro",
            description="Super telephone",
            price=1200.00,
            currency="USD",
            category="Phones",
        )

    def test_create_analytics_event(self):
        event = AnalyticsEvent.objects.create(
            event_type="whatsapp_click",
            source="listing_detail",
            business=self.business,
            listing=self.listing,
            metadata={"title": "iPhone 13 Pro"},
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
        )

        self.assertEqual(event.event_type, "whatsapp_click")
        self.assertEqual(event.source, "listing_detail")
        self.assertEqual(event.business, self.business)
        self.assertEqual(event.listing, self.listing)
        self.assertEqual(event.metadata["title"], "iPhone 13 Pro")
        self.assertEqual(event.ip_address, "127.0.0.1")
        self.assertEqual(event.user_agent, "Mozilla/5.0")
        self.assertIsNotNone(event.created_at)


class AnalyticsAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone_whatsapp="243899530506",
            password="testpassword123",
        )
        self.business = self.user.business
        self.business.name = "Boutique Test"
        self.business.business_type = "SHOP"
        self.business.save()
        self.listing = Listing.objects.create(
            business=self.business,
            title="iPhone 13 Pro",
            description="Super telephone",
            price=1200.00,
            currency="USD",
            category="Phones",
        )

    def test_post_analytics_event_public_success(self):
        response = self.client.post(
            "/api/analytics/events/",
            {
                "event_type": "whatsapp_click",
                "source": "listing_detail",
                "listing_slug": self.listing.slug,
                "business_slug": self.business.slug,
                "metadata": {"custom_tag": "test"},
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(AnalyticsEvent.objects.count(), 1)
        event = AnalyticsEvent.objects.first()
        self.assertEqual(event.event_type, "whatsapp_click")
        self.assertEqual(event.listing, self.listing)
        self.assertEqual(event.business, self.business)

    def test_post_analytics_event_invalid_type(self):
        response = self.client.post(
            "/api/analytics/events/",
            {
                "event_type": "invalid_type",
                "source": "listing_detail",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_vendor_summary_anonymous(self):
        response = self.client.get("/api/analytics/vendor-summary/")

        self.assertEqual(response.status_code, 401)

    def test_vendor_summary_authenticated(self):
        self.client.force_authenticate(user=self.user)
        AnalyticsEvent.objects.create(
            event_type="whatsapp_click",
            source="listing_detail",
            business=self.business,
            listing=self.listing,
        )
        AnalyticsEvent.objects.create(
            event_type="whatsapp_click",
            source="listing_card",
            business=self.business,
            listing=self.listing,
        )
        old_event = AnalyticsEvent.objects.create(
            event_type="whatsapp_click",
            source="listing_detail",
            business=self.business,
            listing=self.listing,
        )
        AnalyticsEvent.objects.filter(id=old_event.id).update(
            created_at=timezone.now() - datetime.timedelta(days=10)
        )

        response = self.client.get("/api/analytics/vendor-summary/")

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data["active_listings"], 1)
        self.assertEqual(data["whatsapp_clicks_total"], 3)
        self.assertEqual(data["whatsapp_clicks_7d"], 2)
        self.assertEqual(len(data["top_listings"]), 1)
        self.assertEqual(data["top_listings"][0]["slug"], self.listing.slug)
        self.assertEqual(data["top_listings"][0]["whatsapp_clicks"], 3)
