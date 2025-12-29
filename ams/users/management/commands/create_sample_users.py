"""Module for the custom Django create_sample_users command."""

from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import management

from ams.utils.management.commands._constants import LOG_HEADER


class Command(management.base.BaseCommand):
    """Required command class for the custom Django create_sample_users command."""

    help = "Create sample user accounts."

    def create_user(self, email, username, first_name, last_name, password):
        """Create a user with the given details or ensure they exist."""
        User = get_user_model()  # noqa: N806

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
                password=password,
                first_name=first_name,
                last_name=last_name,
                username=username,
            )
            EmailAddress.objects.create(
                user=user,
                email=user.email,
                primary=True,
                verified=True,
            )
            self.stdout.write(f"✅ User '{email}' created.\n")

    def handle(self, *args, **options):
        """Automatically called when the create_sample_users command is given."""
        self.stdout.write(LOG_HEADER.format("👤 Create user accounts"))

        password = settings.SAMPLE_DATA_USER_PASSWORD

        self.create_user(
            email=settings.SAMPLE_DATA_USER_EMAIL,
            username="user",
            first_name="Sample",
            last_name="User",
            password=password,
        )

        self.create_user(
            email="user2@example.com",
            username="user2",
            first_name="Sample",
            last_name="User Two",
            password=password,
        )

        self.create_user(
            email="user3@example.com",
            username="user3",
            first_name="Sample",
            last_name="User Three",
            password=password,
        )
