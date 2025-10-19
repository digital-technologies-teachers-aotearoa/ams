from django.contrib import admin

from .models import XeroContact
from .models import XeroMutex


@admin.register(XeroContact)
class XeroContactAdmin(admin.ModelAdmin):
    list_display = ("account", "contact_id")
    search_fields = (
        "contact_id",
        "account__organisation__name",
        "account__user__email",
    )


@admin.register(XeroMutex)
class XeroMutexAdmin(admin.ModelAdmin):
    list_display = ("__str__",)
