from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ams.memberships.forms import MembershipOptionForm
from ams.memberships.models import IndividualMembership
from ams.memberships.models import MembershipOption
from ams.memberships.models import OrganisationMembership


@admin.register(MembershipOption)
class MembershipOptionAdmin(admin.ModelAdmin):
    form = MembershipOptionForm
    list_display = (
        "order",
        "name",
        "type",
        "duration_display",
        "cost",
        "max_seats",
        "max_charged_seats",
        "archived",
    )
    list_display_links = ("name",)
    list_editable = ("order",)
    search_fields = ("name",)
    list_filter = ("type", "archived")

    def get_fieldsets(self, request, obj=None):
        return (
            (
                None,
                {
                    "fields": ("name",),
                },
            ),
            (
                "Properties",
                {
                    "fields": (
                        "type",
                        "duration_display" if obj else "duration",
                        "cost",
                        "max_seats",
                        "max_charged_seats",
                        "voting_rights",
                    ),
                    "description": "Note: These values are read only after creation.",
                },
            ),
            (
                "Billing",
                {
                    "fields": ("invoice_due_days", "invoice_reference"),
                },
            ),
            (
                "Visibility",
                {
                    "fields": (
                        "order",
                        "archived",
                    ),
                },
            ),
        )

    def get_readonly_fields(self, request, obj=None):
        """Fields are read only on updates only."""
        if obj:
            return (*tuple(MembershipOption.IMMUTABLE_FIELDS), "duration_display")
        return ()

    def duration_display(self, obj):
        return obj.duration_display

    def delete_model(self, request, obj):
        """Handle deletion with proper ValidationError handling."""
        try:
            super().delete_model(request, obj)
        except ValidationError as e:
            # Extract message from ValidationError (can be string, list, or dict)
            if hasattr(e, "message"):
                msg = e.message
            elif hasattr(e, "messages"):
                msg = " ".join(e.messages)
            else:
                msg = str(e)
            self.message_user(request, msg, messages.ERROR)

    def delete_queryset(self, request, queryset):
        """Handle bulk deletion with partial success support."""
        failed_deletions = []
        success_count = 0

        for obj in queryset:
            try:
                obj.delete()
                success_count += 1
            except ValidationError:
                failed_deletions.append(str(obj))

        if failed_deletions:
            msg = _(
                "Could not delete the following membership options because they have "
                "existing memberships. Archive them instead: {}",
            ).format(", ".join(failed_deletions))
            self.message_user(request, msg, messages.ERROR)

        if success_count > 0:
            self.message_user(
                request,
                _("Successfully deleted {} membership option(s).").format(
                    success_count,
                ),
                messages.SUCCESS,
            )

    def delete_view(self, request, object_id, extra_context=None):
        """Override to prevent success message when deletion fails."""
        obj = self.get_object(request, object_id)
        if obj is None:
            # Object doesn't exist, let parent handle it
            return super().delete_view(request, object_id, extra_context)

        obj_display = str(obj)

        # Handle POST (actual deletion)
        if request.method == "POST":
            # Call delete_model - it catches ValidationError and shows error message
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
            return HttpResponseRedirect(
                reverse(
                    f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist",  # noqa: SLF001
                ),
            )

        # For GET requests, show the default confirmation page
        return super().delete_view(request, object_id, extra_context)


@admin.register(IndividualMembership)
class IndividualMembershipAdmin(admin.ModelAdmin):
    list_display = (
        "user_display",
        "membership_option",
        "status",
        "start_date",
        "expiry_date",
        "approved_datetime",
    )
    search_fields = ("user__email", "membership_option__name")
    list_filter = ("membership_option", "start_date")
    autocomplete_fields = ["user", "membership_option"]
    readonly_fields = ("user_display", "status")
    exclude = ("user",)

    fields = (
        "user_display",
        "membership_option",
        "start_date",
        "expiry_date",
        "approved_datetime",
        "status",
    )

    @admin.display(
        description="User",
    )
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.get_full_name()} ({obj.user.email})"
        return "-"

    def status(self, obj):
        return obj.get_status_display()


@admin.register(OrganisationMembership)
class OrganisationMembershipAdmin(admin.ModelAdmin):
    list_display = (
        "organisation",
        "membership_option",
        "status",
        "occupied_seats",
        "seats",
        "start_date",
        "expiry_date",
    )
    search_fields = ("organisation__name", "membership_option__name")
    list_filter = ("start_date",)
    autocomplete_fields = ["organisation", "membership_option"]
    readonly_fields = (
        "organisation",
        "status",
        "occupied_seats",
    )

    fields = (
        "organisation",
        "membership_option",
        "status",
        "occupied_seats",
        "seats",
        "start_date",
        "expiry_date",
        "approved_datetime",
    )

    @admin.display(
        description="Status",
    )
    def status(self, obj):
        return obj.get_status_display()
