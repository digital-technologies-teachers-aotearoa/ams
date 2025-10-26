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
        email = settings.SAMPLE_DATA_USER_EMAIL

        existing_user = User.objects.filter(email=email).first()
        if existing_user:
            # Ensure email address object exists and is verified
            EmailAddress.objects.get_or_create(
                user=existing_user,
                email=existing_user.email,
                defaults={"primary": True, "verified": True},
            )
            self.stdout.write(f"✅ User '{email}' already exists. Skipping creation.\n")
        else:
            user = User.objects.create_user(
                email=email,
                password=settings.SAMPLE_DATA_USER_PASSWORD,
                first_name="Sample",
                last_name="User",
                username="user",
            )
            EmailAddress.objects.create(
                user=user,
                email=user.email,
                primary=True,
                verified=True,
            )
            self.stdout.write("✅ User account created.\n")
