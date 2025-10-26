"""Module for the custom Django create_sample_admin command."""

from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import management

from ams.utils.management.commands._constants import LOG_HEADER


class Command(management.base.BaseCommand):
    """Required command class for the custom Django create_sample_admin command."""

    help = "Create admin account."

    def handle(self, *args, **options):
        """Automatically called when the create_sample_admin command is given."""
        self.stdout.write(LOG_HEADER.format("👷 Create admin account"))

        User = get_user_model()  # noqa: N806
        email = settings.SAMPLE_DATA_ADMIN_EMAIL
        password = settings.SAMPLE_DATA_ADMIN_PASSWORD

        admin = User.objects.filter(email=email).first()
        if admin:
            updated = False
            if not admin.is_superuser or not admin.is_staff:
                admin.is_superuser = True
                admin.is_staff = True
                admin.save(update_fields=["is_superuser", "is_staff"])
                updated = True
            if updated:
                self.stdout.write("🔧 Existing admin account updated.\n")
            else:
                self.stdout.write("✅ Admin account already exists.\n")
        else:
            admin = User.objects.create_superuser(
                email=email,
                password=password,
                first_name="Admin",
                last_name="Account",
                username="admin",
            )
            self.stdout.write("✅ Admin account created.\n")

        if not EmailAddress.objects.filter(user=admin, email=admin.email).exists():
            EmailAddress.objects.create(
                user=admin,
                email=admin.email,
                primary=True,
                verified=True,
            )
