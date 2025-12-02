"""Management command to ensure required CMS pages exist."""

from django.conf import settings
from django.core import management
from django.core.management.base import BaseCommand
from wagtail.models import Locale
from wagtail.models import Page
from wagtail.models import Site

from ams.cms.models import HomePage
from ams.cms.models import SiteSettings
from ams.utils.management.commands._constants import LOG_HEADER


class Command(BaseCommand):
    help = "Ensure required CMS pages exist and set up language-specific sites"

    def handle(self, *args, **options):
        self.stdout.write(LOG_HEADER.format("📋 Check required CMS pages"))

        # Domain configuration from settings
        base_domain = settings.SITE_DOMAIN
        base_port = settings.SITE_PORT

        # Get or create root page
        try:
            root_page = Page.objects.get(depth=1)
        except Page.DoesNotExist:
            self.stdout.write(
                self.style.ERROR("Root page not found. Run migrations first."),
            )
            return

        # Ensure site constaint is removed
        management.call_command("modify_site_hostname_constraint", "--remove")

        # Process each language from settings.LANGUAGES
        created_locales = []
        language_sites = []
        managed_site_ids = []

        for lang_code, lang_name in settings.LANGUAGES:
            # Ensure locale exists
            locale, _ = Locale.objects.get_or_create(
                language_code=lang_code,
            )
            created_locales.append(str(locale))

            # Create or update home page
            home, created = HomePage.objects.update_or_create(
                locale=locale,
                defaults={
                    "title": "Home",
                    "slug": f"{lang_code}",
                },
            )

            # If newly created, add it as a child of root page
            if created:
                root_page.add_child(instance=home)

            action = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ {action} {lang_name} home page: {home}",
                ),
            )

            # Create or update site for this language
            # English language is the default site
            site, created = Site.objects.update_or_create(
                hostname=base_domain,
                sitesettings__language=lang_code,
                defaults={
                    "root_page": home,
                    "site_name": f"{lang_name} Site",
                    "is_default_site": lang_code == "en",
                    "port": base_port,
                },
            )
            if created:
                SiteSettings.objects.update_or_create(
                    site=site,
                    defaults={
                        "language": lang_code,
                    },
                )
            action = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(f"✅ {action} {lang_name} site: {site}"),
            )
            language_sites.append((lang_code, lang_name))
            managed_site_ids.append(site.id)

        # Delete any sites not managed by this command
        deleted_sites = Site.objects.exclude(id__in=managed_site_ids)
        deleted_count = deleted_sites.count()
        if deleted_count > 0:
            deleted_sites.delete()
            self.stdout.write(
                self.style.WARNING(
                    f"🗑️  Deleted {deleted_count} unmanaged site(s)",
                ),
            )

        # Summary output
        self.stdout.write(
            self.style.SUCCESS("\n✅ Site setup complete!"),
        )
        self.stdout.write(f"✅ Locales: {', '.join(created_locales)}")
        self.stdout.write("\nYour sites are now accessible at:")
        for lang_code, lang_name in language_sites:
            protocol = "http" if base_domain == "localhost" else "https"
            port_suffix = f":{base_port}" if base_port != 80 else ""  # noqa: PLR2004
            self.stdout.write(
                f"  • {lang_name}: {protocol}://{base_domain}{port_suffix}/{lang_code}/",
            )
