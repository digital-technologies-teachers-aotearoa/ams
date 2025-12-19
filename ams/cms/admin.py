"""Admin configuration for CMS models."""

from django.contrib import admin
from wagtail.contrib.settings.forms import SiteSwitchForm

from ams.cms.models import ThemeSettingsRevision


@admin.register(ThemeSettingsRevision)
class ThemeSettingsRevisionAdmin(admin.ModelAdmin):
    """Admin interface for viewing theme settings revision history."""

    list_display = ["id", "settings", "created_at"]
    list_filter = ["created_at", "settings"]
    readonly_fields = ["settings", "data", "created_at"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    def has_add_permission(self, request):
        """Revisions are created automatically, not manually."""
        return False

    def has_change_permission(self, request, obj=None):
        """Revisions are read-only."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion of old revisions for cleanup."""
        return True


# Monkey-patch SiteSwitchForm to use Site.__str__ representation
# Can be removed if https://github.com/wagtail/wagtail/pull/13608 is merged.


def custom_init(self, current_site, model, sites, **kwargs):
    """Override to use custom site display in dropdown."""
    initial_data = {"site": self.get_change_url(current_site, model)}
    # Call parent Form.__init__ directly instead of going through original
    super(SiteSwitchForm, self).__init__(initial=initial_data, **kwargs)

    # Use str(site) instead of hardcoded site.hostname
    self.fields["site"].choices = [
        (
            self.get_change_url(site, model),
            str(site),  # This now uses our monkey-patched Site.__str__
        )
        for site in sites
    ]


SiteSwitchForm.__init__ = custom_init
