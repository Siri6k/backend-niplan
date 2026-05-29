# Generated manually for the analytics app.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("base_api", "0009_otpcode_is_used_alter_otpcode_phone_number_and_more"),
        ("listing", "0004_remove_verificationrequest_doc_front_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="AnalyticsEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(choices=[("whatsapp_click", "WhatsApp click"), ("listing_view", "Listing view"), ("business_view", "Business view")], max_length=40)),
                ("source", models.CharField(max_length=80)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("business", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="analytics_events", to="base_api.business")),
                ("listing", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="analytics_events", to="listing.listing")),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["event_type", "-created_at"], name="analytics_a_event_t_7d1a4f_idx"),
                    models.Index(fields=["business", "event_type", "-created_at"], name="analytics_a_busines_f9e5ff_idx"),
                    models.Index(fields=["listing", "event_type", "-created_at"], name="analytics_a_listing_8a6da6_idx"),
                ],
            },
        ),
    ]
