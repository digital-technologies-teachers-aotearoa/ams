from django.urls import path

from ams.billing.providers.xero.views import invoice_detail
from ams.billing.providers.xero.views import invoice_redirect
from ams.billing.providers.xero.views import xero_webhooks

app_name = "billing"
urlpatterns = [
    path("invoice/<slug:invoice_number>/", invoice_redirect, name="invoice-redirect"),
    path(
        "invoice/<slug:invoice_number>/detail/",
        invoice_detail,
        name="invoice-detail",
    ),
    path("xero/webhooks/", xero_webhooks, name="xero-webhooks"),
]
