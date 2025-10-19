from django.contrib import admin

from ams.memberships.forms import MembershipOptionForm
from ams.memberships.models import IndividualMembership
from ams.memberships.models import MembershipOption
from ams.memberships.models import OrganisationMembership


@admin.register(MembershipOption)
class MembershipOptionAdmin(admin.ModelAdmin):
    form = MembershipOptionForm
    list_display = ("name", "type", "duration_display", "cost")
    search_fields = ("name",)
    list_filter = ("type",)


@admin.register(IndividualMembership)
class IndividualMembershipAdmin(admin.ModelAdmin):
    list_display = (
        "user_display",
        "membership_option",
        "status",
        "start_date",
        "expiry_date",
        "approved_datetime",
        "invoice",
    )
    search_fields = ("user__email", "membership_option__name")
    list_filter = ("membership_option", "start_date")
    autocomplete_fields = ["user", "membership_option", "invoice"]
    readonly_fields = ("user_display", "status")
    exclude = ("user",)

    fields = (
        "user_display",
        "membership_option",
        "start_date",
        "expiry_date",
        "approved_datetime",
        "invoice",
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
        "status_display",
        "start_date",
        "expiry_date",
        "invoice",
    )
    search_fields = ("organisation__name", "membership_option__name")
    list_filter = ("membership_option", "start_date")
    autocomplete_fields = ["organisation", "membership_option", "invoice"]

    fields = (
        "organisation",
        "membership_option",
        "start_date",
        "expiry_date",
        "invoice",
        "status",
    )

    @admin.display(
        description="Status",
    )
    def status_display(self, obj):
        return (
            obj.get_status_display()
            if hasattr(obj, "get_status_display")
            else obj.status()
        )
