"""Admin configuration for CMS models."""

from django.contrib import admin
from django.contrib.admin.utils import quote
from django.contrib.admin.utils import unquote
from django.shortcuts import get_object_or_404
from django.urls import reverse
from wagtail.contrib.settings.forms import SiteSwitchForm
from wagtail.models import Site
from wagtailmenus.menuadmin import MainMenuEditView

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


# Monkey-patch MainMenuEditView to fix integer quote/unquote bug
# Can be removed when wagtailmenus fixes Django 5.x compatibility upstream
def fixed_main_menu_setup(self, request, *args, **kwargs):
    """Fixed setup method that converts pk to string before unquoting."""
    # Convert pk to string before passing to unquote
    self.site = get_object_or_404(Site, id=unquote(str(kwargs["pk"])))

    # Call parent's setup (skip MainMenuEditView's broken version)
    super(MainMenuEditView, self).setup(request, *args, **kwargs)

    self.site_switcher = None
    if Site.objects.count() > 1:
        self.site_switcher = SiteSwitchForm(self.site, self.edit_url_name)


def fixed_get_edit_url(self):
    """Fixed get_edit_url that converts pk to string before quoting."""
    # Convert pk to string before passing to quote
    return reverse(self.edit_url_name, args=(quote(str(self.site.pk)),))


# Apply the monkey patches
MainMenuEditView.setup = fixed_main_menu_setup
MainMenuEditView.get_edit_url = fixed_get_edit_url
