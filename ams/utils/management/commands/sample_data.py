"""Module for the custom Django sample_data command."""

from django.conf import settings
from django.core import management

from ams.utils.management.commands._constants import LOG_HEADER


class Command(management.base.BaseCommand):
    """Required command class for the custom Django sample_data command."""

    help = "Add sample data to database."

    def add_arguments(self, parser):
        """Interprets arguments passed to command."""

        parser.add_argument(
            "--flush",
            action="store_true",
            help="Flushes the database before adding sample data.",
        )

    def handle(self, *args, **options):
        """Automatically called when the sampledata command is given."""
        if settings.DEPLOYED:
            message = "This command can only be executed on a non-production website."
            raise management.base.CommandError(message)

        # Clear all data
        if options["flush"]:
            self.stdout.write(LOG_HEADER.format("💾 Wipe database"))
            management.call_command("flush", interactive=False)
            management.call_command("loaddata", "wagtailcore_initial_data")
            management.call_command("loaddata", "wagtailimages_initial_data")
            self.stdout.write("✅ Database wiped.")

        # Create accounts
        management.call_command("create_sample_admin")
        management.call_command("create_sample_user")

        # Create membership options
        management.call_command("create_sample_membership_options")

        # Check CMS pages
        management.call_command("ensure_required_cms_pages")
