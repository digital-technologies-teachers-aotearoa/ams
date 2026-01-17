"""Django admin configuration for terms app."""

from django.contrib import admin
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseRedirect
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

    def delete_model(self, request, obj):
        """Handle deletion with proper ProtectedError handling."""
        try:
            super().delete_model(request, obj)
        except ProtectedError:
            msg = _(
                "Cannot delete this term version because users have accepted it. Term "
                "versions with acceptances are protected to maintain audit history.",
            )
            self.message_user(request, msg, messages.ERROR)

    def delete_queryset(self, request, queryset):
        """Handle bulk deletion with partial success support."""
        failed_deletions = []
        success_count = 0

        for obj in queryset:
            try:
                obj.delete()
                success_count += 1
            except ProtectedError:
                failed_deletions.append(str(obj))

        if failed_deletions:
            msg = _(
                "Could not delete the following term versions because they have "
                "user acceptances: {}",
            ).format(", ".join(failed_deletions))
            self.message_user(request, msg, messages.ERROR)

        if success_count > 0:
            self.message_user(
                request,
                _("Successfully deleted {} term version(s).").format(success_count),
                messages.SUCCESS,
            )

    def delete_view(self, request, object_id, extra_context=None):
        """Override to prevent success message when deletion fails."""
        obj = self.get_object(request, object_id)
        if obj is None:
            return super().delete_view(request, object_id, extra_context)

        obj_display = str(obj)

        # Handle POST (actual deletion)
        if request.method == "POST":
            # Call delete_model - it catches ProtectedError and shows error message
            self.delete_model(request, obj)

            # Check if object actually still exists (deletion failed)
            if self.model.objects.filter(pk=object_id).exists():
                # Deletion failed - error message already shown by delete_model
                # Redirect to change view without success message
                return HttpResponseRedirect(request.path)
            # Deletion succeeded - show success message
            self.message_user(
                request,
                _('The %(name)s "%(obj)s" was deleted successfully.')
                % {
                    "name": self.model._meta.verbose_name,  # noqa: SLF001
                    "obj": obj_display,
                },
                messages.SUCCESS,
            )
            # Redirect to list view
            return HttpResponseRedirect(self.get_success_url())

        # For GET requests, show the default confirmation page
        return super().delete_view(request, object_id, extra_context)


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
