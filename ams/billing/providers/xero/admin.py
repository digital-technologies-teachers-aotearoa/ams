from django.contrib import admin

from .models import XeroContact


@admin.register(XeroContact)
class XeroContactAdmin(admin.ModelAdmin):
    """Django admin configuration for XeroContact model.

    Provides a list view displaying account and contact_id, with search
    capabilities across contact IDs, organization names, and user emails.
    """

    list_display = ("account", "contact_id")
    search_fields = (
        "contact_id",
        "account__organisation__name",
        "account__user__email",
    )
