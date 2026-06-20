from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ams.organisations.models import Organisation
from ams.organisations.models import OrganisationMember


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "email", "contact_name", "is_active")
    search_fields = ("name", "email", "contact_name")
    list_filter = ("is_active",)
    actions = ["activate_organisations", "deactivate_organisations"]
    fieldsets = (
        (
            None,
            {
                "fields": ("name",),
            },
        ),
        (
            _("Contact"),
            {
                "fields": (
                    "contact_name",
                    "email",
                    "telephone",
                ),
            },
        ),
        (
            _("Physical address"),
            {
                "fields": (
                    "street_address",
                    "suburb",
                    "city",
                ),
            },
        ),
        (
            _("Postal address"),
            {
                "fields": (
                    "postal_address",
                    "postal_suburb",
                    "postal_city",
                    "postal_code",
                ),
            },
        ),
    )

    @admin.action(description=_("Activate selected organisations"))
    def activate_organisations(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description=_("Deactivate selected organisations"))
    def deactivate_organisations(self, request, queryset):
        # Use save() to trigger auto-cancellation logic
        for org in queryset:
            org.is_active = False
            org.save()


@admin.register(OrganisationMember)
class OrganisationMemberAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "organisation",
        "invite_email",
        "role",
        "accepted_datetime",
    )
    search_fields = ("user__email", "organisation__name", "invite_email")
    list_filter = ("organisation", "role")
