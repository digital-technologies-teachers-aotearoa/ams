"""Management command to ensure required CMS pages exist."""

from django.conf import settings
from django.core.management.base import BaseCommand
from wagtail.models import Locale
from wagtail.models import Page
from wagtail.models import Site

from ams.cms.models import HomePage
from ams.utils.management.commands._constants import LOG_HEADER


class Command(BaseCommand):
    help = "Ensure required CMS pages exist and set up language-specific sites"

    def handle(self, *args, **options):
        self.stdout.write(LOG_HEADER.format("📋 Check required CMS pages"))

        # Domain configuration
        base_domain = "localhost:3000"

        # Get or create root page
        try:
            root_page = Page.objects.get(depth=1)
        except Page.DoesNotExist:
            self.stdout.write(
                self.style.ERROR("Root page not found. Run migrations first."),
            )
            return

        # Process each language from settings.LANGUAGES
        created_locales = []
        language_sites = []

        for lang_code, lang_name in settings.LANGUAGES:
            # Ensure locale exists
            locale, _ = Locale.objects.get_or_create(
                language_code=lang_code,
            )
            created_locales.append(str(locale))

            # Create home page if it doesn't exist
            home = HomePage.objects.filter(locale=locale).first()
            if not home:
                home = HomePage(
                    title=f"{lang_name} Home",
                    slug=f"{lang_code}",
                    locale=locale,
                )
                root_page.add_child(instance=home)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Created {lang_name} home page: {home}",
                    ),
                )
            else:
                self.stdout.write(
                    f"✅ {lang_name} home page already exists: {home}",
                )

            # Create or update site for this language
            # English language is the default site
            site, created = Site.objects.update_or_create(
                hostname=lang_code,
                defaults={
                    "root_page": home,
                    "site_name": f"{lang_name} Site",
                    "is_default_site": lang_code == "en",
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(f"✅ {action} {lang_name} site: {site}"),
            )
            language_sites.append((lang_code, lang_name))

        # Summary output
        self.stdout.write(f"✅ Locales: {', '.join(created_locales)}")
        self.stdout.write(
            self.style.SUCCESS("\n✅ Site setup complete!"),
        )
        self.stdout.write("\nYour sites are now accessible at:")
        for lang_code, lang_name in language_sites:
            self.stdout.write(f"  • {lang_name}: http://{base_domain}/{lang_code}/")
