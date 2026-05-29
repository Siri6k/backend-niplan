from django.urls import path

from analytics.views import AnalyticsEventCreateView, VendorAnalyticsSummaryView


urlpatterns = [
    path("events/", AnalyticsEventCreateView.as_view(), name="analytics-event-create"),
    path("vendor-summary/", VendorAnalyticsSummaryView.as_view(), name="vendor-analytics-summary"),
]
