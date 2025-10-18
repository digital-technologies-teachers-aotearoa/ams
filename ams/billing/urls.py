from django.urls import path

from ams.billing.providers.xero.views import xero_webhooks

app_name = "billing"
urlpatterns = [
    path("xero/webhooks/", xero_webhooks, name="xero-webhooks"),
]
