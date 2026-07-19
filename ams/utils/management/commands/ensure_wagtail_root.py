"""Module for the custom Django ensure_wagtail_root command."""

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core import management
from wagtail.coreutils import get_supported_content_language_variant
from wagtail.models import Collection
from wagtail.models import GroupPagePermission
from wagtail.models import Locale
from wagtail.models import Page
from wagtail.models import Site

from ams.utils.management.commands._constants import LOG_HEADER


class Command(management.base.BaseCommand):
    """Required command class for the custom Django ensure_wagtail_root command."""

    help = (
        "Recreate Wagtail's default locale, root Page, and root Collection if "
        "missing. manage.py flush truncates data without replaying migrations, "
        "which deletes these rows (created by wagtail's own 0054_initial_locale, "
        "0002_initial_data, and 0025_collection_initial_data migrations) without "
        "restoring them, breaking setup_cms and anything else that depends on a "
        "root page existing."
    )

    def handle(self, *args, **options):
        """Automatically called when the ensure_wagtail_root command is given."""
        self.stdout.write(
            LOG_HEADER.format("🌳 Ensure Wagtail root page and collection"),
        )

        if Locale.objects.filter(
            language_code=get_supported_content_language_variant(
                settings.LANGUAGE_CODE,
            ),
        ).exists():
            self.stdout.write("✅ Default locale already exists.\n")
        else:
            Locale.objects.create(
                language_code=get_supported_content_language_variant(
                    settings.LANGUAGE_CODE,
                ),
            )
            self.stdout.write("✅ Default locale created.\n")

        if Page.objects.filter(depth=1).exists():
            self.stdout.write("✅ Root page already exists.\n")
        else:
            page_content_type, _ = ContentType.objects.get_or_create(
                model="page",
                app_label="wagtailcore",
            )
            root = Page.objects.create(
                title="Root",
                slug="root",
                content_type=page_content_type,
                path="0001",
                depth=1,
                numchild=1,
                url_path="/",
            )
            homepage = Page.objects.create(
                title="Welcome to your new Wagtail site!",
                slug="home",
                content_type=page_content_type,
                path="00010001",
                depth=2,
                numchild=0,
                url_path="/home/",
            )
            Site.objects.create(
                hostname="localhost",
                root_page_id=homepage.id,
                is_default_site=True,
            )

            moderators_group, _ = Group.objects.get_or_create(name="Moderators")
            editors_group, _ = Group.objects.get_or_create(name="Editors")
            page_permissions = {
                permission.codename: permission
                for permission in Permission.objects.filter(
                    content_type=page_content_type,
                )
            }
            for codename in ("add_page", "change_page", "publish_page"):
                GroupPagePermission.objects.get_or_create(
                    group=moderators_group,
                    page=root,
                    permission=page_permissions[codename],
                )
            for codename in ("add_page", "change_page"):
                GroupPagePermission.objects.get_or_create(
                    group=editors_group,
                    page=root,
                    permission=page_permissions[codename],
                )
            self.stdout.write("✅ Root page created.\n")

        if Collection.objects.filter(depth=1).exists():
            self.stdout.write("✅ Root collection already exists.\n")
        else:
            Collection.objects.create(name="Root", path="0001", depth=1, numchild=0)
            self.stdout.write("✅ Root collection created.\n")
