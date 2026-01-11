"""Django admin configuration for terms app."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ams.terms.models import TermAcceptance
from ams.terms.models import TermVersion


@admin.register(TermVersion)
class TermVersionAdmin(admin.ModelAdmin):
    """Django admin interface for managing Term Versions."""

    list_display = [
        "term",
        "version",
        "is_active",
        "date_active",
        "created_at",
    ]
    list_filter = ["term", "is_active", "date_active", "created_at"]
    search_fields = ["version", "content"]
    ordering = ["-date_active", "-created_at"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "date_active"

    fieldsets = (
        (
            _("Version Info"),
            {
                "fields": ("term", "version"),
            },
        ),
        (
            _("Activation"),
            {
                "fields": ("is_active", "date_active"),
            },
        ),
        (
            _("Content"),
            {
                "fields": ("content", "change_log"),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(TermAcceptance)
class TermAcceptanceAdmin(admin.ModelAdmin):
    """Django admin interface for viewing Term Acceptances (read-only)."""

    list_display = [
        "user",
        "term_version",
        "accepted_at",
        "ip_address",
        "source",
    ]
    list_filter = ["term_version__term", "source", "accepted_at"]
    search_fields = ["user__email", "user__username", "ip_address"]
    ordering = ["-accepted_at"]
    readonly_fields = [
        "user",
        "term_version",
        "accepted_at",
        "ip_address",
        "user_agent",
        "source",
    ]
    date_hierarchy = "accepted_at"

    def has_add_permission(self, request):
        """Disable manual creation of acceptances."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable editing of acceptances."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disable deletion of acceptances."""
        return False
