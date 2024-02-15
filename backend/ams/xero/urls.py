from django.urls import path

from .views import xero_webhooks

urlpatterns = [
    path("webhooks/", xero_webhooks, name="xero-webhooks"),
]
