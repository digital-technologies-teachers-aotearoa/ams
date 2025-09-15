"""Module for the custom Django deploy_steps command."""

from django.core import management

from ams.utils.management.commands._constants import LOG_HEADER


class Command(management.base.BaseCommand):
    """Required command class for the custom Django deploy_steps command."""

    help = "Runs steps used in deployments."

    def handle(self, *args, **options):
        self.stdout.write(LOG_HEADER.format("💾 Migrate database"))
        management.call_command("migrate", interactive=False)

        management.call_command("ensure_required_cms_pages")
