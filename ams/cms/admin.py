from wagtail.contrib.settings.forms import SiteSwitchForm

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
