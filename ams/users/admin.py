import csv

from allauth.account.decorators import secure_admin_login
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.db.models import Prefetch
from django.http import StreamingHttpResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ams.memberships.models import IndividualMembership
from ams.memberships.models import MembershipStatus
from ams.organisations.models import OrganisationMember
from ams.users.forms import UserAdminChangeForm
from ams.users.forms import UserAdminCreationForm
from ams.users.models import ProfileField
from ams.users.models import ProfileFieldGroup
from ams.users.models import ProfileFieldResponse
from ams.users.models import User
from ams.users.widgets import OptionsWidget
from ams.users.widgets import TranslationWidget

if settings.DJANGO_ADMIN_FORCE_ALLAUTH:
    # Force the `admin` sign in process to go through the `django-allauth` workflow:
    # https://docs.allauth.org/en/latest/common/admin.html#admin
    admin.autodiscover()
    admin.site.login = secure_admin_login(admin.site.login)  # type: ignore[method-assign]


# --- Profile Field Admin ---
@admin.register(ProfileFieldGroup)
class ProfileFieldGroupAdmin(admin.ModelAdmin):
    """Admin for ProfileFieldGroup."""

    list_display = ["__str__", "order", "active_field_count", "is_active"]
    list_editable = ["order", "is_active"]
    fieldsets = (
        (
            _("Group Info"),
            {
                "fields": ("name_translations", "order", "is_active"),
            },
        ),
        (
            _("Description"),
            {
                "fields": ("description_translations",),
            },
        ),
    )

    @admin.display(
        description=_("Active Fields"),
    )
    def active_field_count(self, obj):
        """Returns count of active fields in group."""
        return obj.fields.filter(is_active=True).count()

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Use custom widgets for translation fields."""
        if db_field.name in ("name_translations", "description_translations"):
            kwargs["widget"] = TranslationWidget()
            kwargs["help_text"] = ""
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(ProfileField)
class ProfileFieldAdmin(admin.ModelAdmin):
    """Admin for ProfileField."""

    list_display = [
        "field_key",
        "__str__",
        "field_type",
        "group",
        "is_read_only",
        "counts_toward_completion",
        "order",
        "is_active",
    ]
    list_filter = [
        "field_type",
        "group",
        "is_read_only",
        "counts_toward_completion",
        "is_active",
    ]
    list_editable = ["order", "is_active"]
    search_fields = ["field_key"]
    fieldsets = (
        (
            _("Basic Info"),
            {
                "fields": ("field_key", "group", "field_type", "order", "is_active"),
            },
        ),
        (
            _("Labels & Help Text"),
            {
                "fields": ("label_translations", "help_text_translations"),
            },
        ),
        (
            _("Options & Constraints"),
            {
                "fields": ("options", "min_value", "max_value"),
            },
        ),
        (
            _("Behaviour"),
            {
                "fields": (
                    "is_read_only",
                    "is_required_for_membership",
                    "counts_toward_completion",
                ),
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        """Make field_key readonly after creation."""
        if obj and obj.pk:
            return ["field_key"]
        return []

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Use custom widgets for translation fields."""
        if db_field.name in ("label_translations", "help_text_translations"):
            kwargs["widget"] = TranslationWidget()
            kwargs["help_text"] = ""
        elif db_field.name == "options":
            kwargs["widget"] = OptionsWidget()
            kwargs["help_text"] = ""
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class ProfileFieldResponseInline(admin.TabularInline):
    model = ProfileFieldResponse
    extra = 0
    fields = ("profile_field", "value", "updated_datetime")
    readonly_fields = ("updated_datetime",)
    autocomplete_fields = ("profile_field",)


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    inlines = [ProfileFieldResponseInline]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "username",
                ),
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "admin_notes",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = ["email", "first_name", "last_name", "username", "is_superuser"]
    search_fields = ["first_name", "last_name"]
    ordering = ["id"]
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "username",
                ),
            },
        ),
    )
    actions = ["export_users_csv"]

    @admin.action(description=_("Export users to CSV"))
    def export_users_csv(self, request, queryset):
        """Export all user data for selected users to CSV."""
        profile_fields = ProfileField.objects.filter(is_active=True).order_by(
            "group__order",
            "order",
        )

        queryset = queryset.prefetch_related(
            "profile_responses__profile_field",
            Prefetch(
                "individual_memberships",
                queryset=IndividualMembership.objects.select_related(
                    "membership_option",
                ).order_by("-created_datetime"),
            ),
            Prefetch(
                "organisation_members",
                queryset=OrganisationMember.objects.active()
                .select_related("organisation")
                .prefetch_related(
                    "organisation__organisation_memberships__membership_option",
                )
                .order_by("-created_datetime"),
            ),
        )

        headers = [
            "Email",
            "First Name",
            "Last Name",
            "Username",
            "Active Member",
            "Date Joined",
            "Last Login",
            "Is Active",
            "Is Staff",
            "Is Superuser",
            "Admin Notes",
            "Individual Membership Status",
            "Membership Option",
            "Membership Start Date",
            "Membership Expiry Date",
            "Organisation Name",
            "Organisation Role",
            "Organisation Membership Status",
        ]
        headers.extend([field.field_key for field in profile_fields])

        class Echo:
            def write(self, value):
                return value

        def generate_rows():
            writer = csv.writer(Echo())
            yield writer.writerow(headers)

            for user in queryset:
                responses_dict = {
                    resp.profile_field.field_key: resp.get_value()
                    for resp in user.profile_responses.all()
                }

                # Individual membership (most recent)
                ind_memberships = list(user.individual_memberships.all())
                if ind_memberships:
                    ind = ind_memberships[0]
                    ind_status = ind.status()
                    ind_option = ind.membership_option.name
                    ind_start = ind.start_date
                    ind_expiry = ind.expiry_date
                else:
                    ind_status = MembershipStatus.NONE
                    ind_option = ""
                    ind_start = ""
                    ind_expiry = ""

                # Organisation membership (most recent active org member)
                org_members = list(user.organisation_members.all())
                if org_members:
                    org_member = org_members[0]
                    org_name = org_member.organisation.name
                    org_role = org_member.get_role_display()
                    org_membership = org_member.organisation.get_active_membership()
                    org_status = (
                        org_membership.status()
                        if org_membership
                        else MembershipStatus.NONE
                    )
                else:
                    org_name = ""
                    org_role = ""
                    org_status = ""

                row = [
                    user.email,
                    user.first_name,
                    user.last_name,
                    user.username,
                    user.check_has_active_membership_core(),
                    user.date_joined.strftime("%Y-%m-%d %H:%M:%S"),
                    (
                        user.last_login.strftime("%Y-%m-%d %H:%M:%S")
                        if user.last_login
                        else ""
                    ),
                    user.is_active,
                    user.is_staff,
                    user.is_superuser,
                    user.admin_notes,
                    ind_status,
                    ind_option,
                    ind_start,
                    ind_expiry,
                    org_name,
                    org_role,
                    org_status,
                ]

                for field in profile_fields:
                    value = responses_dict.get(field.field_key, "")
                    if isinstance(value, list):
                        value = ", ".join(str(v) for v in value)
                    row.append(value)

                yield writer.writerow(row)

        filename = f"users_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return StreamingHttpResponse(
            generate_rows(),
            content_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    def get_inlines(self, request, obj=None):
        if obj is None:
            return []
        return super().get_inlines(request, obj)
