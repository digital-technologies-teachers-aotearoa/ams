"""Management command to ensure required CMS pages exist."""

from django.core.management.base import BaseCommand
from wagtail.models import Page
from wagtail.models import Site

from ams.cms.models import AboutPage
from ams.cms.models import HomePage
from ams.utils.management.commands._constants import LOG_HEADER


def get_or_create_page(page_model, title, slug):
    page = page_model.objects.first()
    created = False
    if not page:
        root = Page.get_first_root_node()
        page = page_model(title=title, slug=slug)
        root.add_child(instance=page)
        page.save_revision().publish()
        created = True
    return page, created


class Command(BaseCommand):
    help = "Ensure Home/About/Membership pages exist and set site root to HomePage"

    def handle(self, *args, **options):
        self.stdout.write(LOG_HEADER.format("📋 Check required CMS pages"))

        home, created_home = get_or_create_page(HomePage, "Home", "home")
        _, created_about = get_or_create_page(AboutPage, "About", "about")

        self.stdout.write(f"✅ Home page: {'Created' if created_home else 'Exists'}")
        self.stdout.write(f"✅ About page: {'Created' if created_about else 'Exists'}")

        # Ensure there's a Site pointing to the HomePage
        site = Site.objects.first()
        if site:
            if site.root_page_id != home.id:
                site.root_page = home
                site.save()
                self.stdout.write("✅ Updated default Site to point at HomePage")
            else:
                self.stdout.write("✅ Default Site already points to HomePage")
        else:
            Site.objects.create(
                hostname="localhost",
                root_page=home,
                is_default_site=True,
            )
            self.stdout.write("✅ Created default Site pointing to HomePage")
