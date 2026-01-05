from django.contrib import admin

from ams.memberships.forms import MembershipOptionForm
from ams.memberships.models import IndividualMembership
from ams.memberships.models import MembershipOption
from ams.memberships.models import OrganisationMembership


@admin.register(MembershipOption)
class MembershipOptionAdmin(admin.ModelAdmin):
    form = MembershipOptionForm
    list_display = ("name", "type", "duration_display", "cost", "max_seats", "archived")
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
        )

    def get_readonly_fields(self, request, obj=None):
        """Fields are read only on updates only."""
        if obj:
            return (*tuple(MembershipOption.IMMUTABLE_FIELDS), "duration_display")
        return ()

    def duration_display(self, obj):
        return obj.duration_display


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
