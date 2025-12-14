from django.contrib import admin

from .models import XeroContact
from .models import XeroMutex


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


@admin.register(XeroMutex)
class XeroMutexAdmin(admin.ModelAdmin):
    """Django admin configuration for XeroMutex model.

    Provides minimal admin interface for the mutex table, which exists
    primarily for database-level locking rather than data management.
    """

    list_display = ("__str__",)
