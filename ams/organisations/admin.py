from django.contrib import admin

from ams.organisations.models import Organisation
from ams.organisations.models import OrganisationMember


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ("name", "telephone", "email", "contact_name")
    search_fields = ("name", "email", "contact_name")


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
