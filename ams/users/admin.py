import csv

from allauth.account.decorators import secure_admin_login
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ams.users.forms import UserAdminChangeForm
from ams.users.forms import UserAdminCreationForm
from ams.users.models import ProfileField
from ams.users.models import ProfileFieldGroup
from ams.users.models import User

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


@admin.register(ProfileField)
class ProfileFieldAdmin(admin.ModelAdmin):
    """Admin for ProfileField."""

    list_display = [
        "field_key",
        "__str__",
        "field_type",
        "group",
        "is_read_only",
        "order",
        "is_active",
    ]
    list_filter = ["field_type", "group", "is_read_only", "is_active"]
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
            _("Permissions"),
            {
                "fields": ("is_read_only", "is_required_for_membership"),
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        """Make field_key readonly after creation."""
        if obj and obj.pk:
            return ["field_key"]
        return []


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
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
    actions = ["export_profile_responses_csv"]

    @admin.action(description=_("Export profile responses to CSV"))
    def export_profile_responses_csv(self, request, queryset):
        """Export profile responses for selected users to CSV."""
        # Get all active profile fields
        profile_fields = ProfileField.objects.filter(is_active=True).order_by(
            "group__order",
            "order",
        )

        # Create CSV response
        response = HttpResponse(content_type="text/csv")
        filename = f"profile_responses_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        # Create CSV writer
        writer = csv.writer(response)

        # Write header row
        header = ["Email", "First Name", "Last Name"]
        header.extend([field.field_key for field in profile_fields])
        writer.writerow(header)

        # Write data rows
        for user in queryset.select_related().prefetch_related("profile_responses"):
            # Create dict mapping field_key → value
            responses_dict = {
                resp.profile_field.field_key: resp.get_value()
                for resp in user.profile_responses.all()
            }

            # Build row
            row = [user.email, user.first_name, user.last_name]
            for field in profile_fields:
                value = responses_dict.get(field.field_key, "")
                # Convert lists to comma-separated strings
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                row.append(value)

            writer.writerow(row)

        return response
