from wagtail.users.apps import WagtailUsersAppConfig


class AmsWagtailUsersAppConfig(WagtailUsersAppConfig):
    """Custom AppConfig for `wagtail.users`, registered in place of the
    plain `"wagtail.users"` INSTALLED_APPS entry (see config/settings/base.py)
    so the CMS Users admin uses AMS's UserViewSet instead of Wagtail's
    default one. Kept in its own module (not `ams/users/apps.py`) because
    Django auto-detects AppConfig subclasses by scanning an app's `apps`
    module, and `ams.users` already has its own AppConfig there — two
    candidates in the same module would make that auto-detection ambiguous.
    """

    user_viewset = "ams.users.wagtail_viewsets.UserViewSet"
