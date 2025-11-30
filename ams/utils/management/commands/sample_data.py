"""Module for the custom Django sample_data command."""

from django.conf import settings
from django.core import management
from wagtail.models import Site

from ams.cms.models import AssociationSettings
from ams.utils.management.commands._constants import LOG_HEADER


class Command(management.base.BaseCommand):
    """Required command class for the custom Django sample_data command."""

    help = "Add sample data to database."

    def handle(self, *args, **options):
        """Automatically called when the sampledata command is given."""
        if settings.DEPLOYED:
            message = "This command can only be executed on a non-production website."
            raise management.base.CommandError(message)

        self.stdout.write(LOG_HEADER.format("💾 Migrating database"))
        management.call_command("migrate")
        self.stdout.write("✅ Database migrated.")

        # Create accounts
        management.call_command("create_sample_admin")
        management.call_command("create_sample_user")

        # Create membership options
        management.call_command("create_sample_membership_options")

        # Setup CMS pages
        management.call_command("setup_cms")

        # Set association settings for each site
        self.stdout.write(LOG_HEADER.format("🏢 Setting association settings"))
        for site in Site.objects.all():
            site_settings = site.sitesettings
            if site_settings.language:
                lang_code = site_settings.language.upper()
                association_name = f"{lang_code} AMS"

                (
                    association_settings,
                    created,
                ) = AssociationSettings.objects.get_or_create(
                    site=site,
                )
                association_settings.association_short_name = association_name
                association_settings.association_long_name = association_name
                association_settings.save()

                action = "Created" if created else "Updated"
                msg = (
                    f"✅ {action} association settings for "
                    f"{site.site_name}: {association_name}"
                )
                self.stdout.write(msg)
        self.stdout.write("✅ Association settings configured.")
