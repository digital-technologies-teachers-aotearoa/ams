from django import forms
from django.conf import settings
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ams.resources.models import Resource
from ams.resources.models import ResourceComponent


class ResourcesFeatureFlagMixin:
    """Hides resources admin when RESOURCES_ENABLED is False."""

    def has_module_permission(self, request):
        if settings.RESOURCES_ENABLED:
            return super().has_module_permission(request)
        return False

    def has_add_permission(self, request):
        if settings.RESOURCES_ENABLED:
            return super().has_add_permission(request)
        return False

    def has_change_permission(self, request, obj=None):
        if settings.RESOURCES_ENABLED:
            return super().has_change_permission(request, obj)
        return False

    def has_view_permission(self, request, obj=None):
        if settings.RESOURCES_ENABLED:
            return super().has_view_permission(request, obj)
        return False


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = "__all__"  # noqa: DJ007

    def clean(self):
        cleaned_data = super().clean()
        author_entities = cleaned_data.get("author_entities")
        author_users = cleaned_data.get("author_users")
        entity_count = author_entities.count() if author_entities is not None else 0
        user_count = author_users.count() if author_users is not None else 0
        if entity_count + user_count == 0:
            raise forms.ValidationError(
                _("At least one author (entity or user) must be listed."),
            )
        return cleaned_data


class ResourceComponentInline(admin.StackedInline):
    model = ResourceComponent
    fk_name = "resource"
    extra = 1
    fieldsets = (
        (None, {"fields": ("name",)}),
        (
            "Item",
            {
                "fields": ("component_url", "component_file", "component_resource"),
                "description": _(
                    "Only one of the following fields must be filled for "
                    "each component.",
                ),
            },
        ),
    )


@admin.register(Resource)
class ResourceAdmin(ResourcesFeatureFlagMixin, admin.ModelAdmin):
    form = ResourceForm
    inlines = [ResourceComponentInline]
    list_display = ("name", "datetime_added", "datetime_updated", "published")
    list_filter = ("published",)
    search_fields = ("name",)
    filter_horizontal = ("author_entities", "author_users")
    fieldsets = (
        (None, {"fields": ("name", "description")}),
        (
            "Ownership",
            {
                "description": _(
                    "Resources can be owned by both users and entities.",
                ),
                "fields": ("author_entities", "author_users"),
            },
        ),
        ("Visibility", {"fields": ("published",)}),
    )
