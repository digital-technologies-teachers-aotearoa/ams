"""Module for the custom Django create_sample_user command."""

from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import management

from ams.utils.management.commands._constants import LOG_HEADER


class Command(management.base.BaseCommand):
    """Required command class for the custom Django create_sample_user command."""

    help = "Create admin account."

    def handle(self, *args, **options):
        """Automatically called when the create_sample_user command is given."""

        self.stdout.write(LOG_HEADER.format("👤 Create user account"))

        User = get_user_model()  # noqa: N806
        user = User.objects.create_user(
            email=settings.SAMPLE_DATA_USER_EMAIL,
            password=settings.SAMPLE_DATA_USER_PASSWORD,
            first_name="Sample",
            last_name="User",
        )

        EmailAddress.objects.create(
            user=user,
            email=user.email,
            primary=True,
            verified=True,
        )

        self.stdout.write("✅ User account created.\n")
