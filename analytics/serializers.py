from rest_framework import serializers


class AnalyticsEventCreateSerializer(serializers.Serializer):
    event_type = serializers.ChoiceField(
        choices=["whatsapp_click", "listing_view", "business_view", "share_click"]
    )
    source = serializers.CharField(max_length=80)
    listing_slug = serializers.SlugField(required=False, allow_blank=True)
    business_slug = serializers.SlugField(required=False, allow_blank=True)
    metadata = serializers.DictField(required=False)
