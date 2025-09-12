"""Module for the custom Django sample_data command."""

from django.conf import settings
from django.core import management

from ams.utils.management.commands._constants import LOG_HEADER


class Command(management.base.BaseCommand):
    """Required command class for the custom Django sample_data command."""

    help = "Add sample data to database."

    def handle(self, *args, **options):
        """Automatically called when the sampledata command is given."""
        if settings.DEPLOYED:
            message = "This command can only be executed on a non-production website."
            raise management.base.CommandError(message)

        # Clear all data
        self.stdout.write(LOG_HEADER.format("💾 Wipe database"))
        management.call_command("flush", interactive=False)
        self.stdout.write("✅ Database wiped.")

        # Create admin account
        management.call_command("create_admin")
