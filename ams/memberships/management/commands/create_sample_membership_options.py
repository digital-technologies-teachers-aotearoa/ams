"""Module for the custom Django create_sample_membership_options command."""

from dateutil.relativedelta import relativedelta
from django.core import management

from ams.memberships.models import MembershipOption
from ams.memberships.models import MembershipOptionType
from ams.utils.management.commands._constants import LOG_HEADER


class Command(management.base.BaseCommand):
    """Custom create_sample_membership_options command."""

    help = "Create admin account."

    def handle(self, *args, **options):
        """Automatically called when the command is called."""

        self.stdout.write(LOG_HEADER.format("🎫 Create membership options"))

        MembershipOption.objects.update_or_create(
            name="Sample Individual Membership - 1 Month",
            type=MembershipOptionType.INDIVIDUAL,
            defaults={
                "duration": relativedelta(months=1),
                "cost": 49.99,
                "invoice_reference": "AMS Membership",
                "description": (
                    "Perfect for trying out our membership benefits with a one-month "
                    "commitment."
                ),
            },
        )
        MembershipOption.objects.update_or_create(
            name="Sample Individual Membership - 1 Year",
            type=MembershipOptionType.INDIVIDUAL,
            defaults={
                "duration": relativedelta(years=1),
                "cost": 499.99,
                "invoice_reference": "AMS Membership",
            },
        )
        MembershipOption.objects.update_or_create(
            name="Free Individual Membership - 1 Day",
            type=MembershipOptionType.INDIVIDUAL,
            defaults={
                "duration": relativedelta(days=1),
                "cost": 0,
                "invoice_reference": "AMS Membership",
                "description": "Free trial membership to explore our community.",
            },
        )
        MembershipOption.objects.update_or_create(
            name="Sample Organisation Membership - 1 Month",
            type=MembershipOptionType.ORGANISATION,
            defaults={
                "duration": relativedelta(months=1),
                "cost": 99.99,
                "invoice_reference": "AMS Membership",
                "archived": False,
                "description": (
                    "Flexible monthly organisation membership with unlimited seats. "
                ),
            },
        )
        MembershipOption.objects.update_or_create(
            name="Sample Organisation Membership - 1 Year",
            type=MembershipOptionType.ORGANISATION,
            defaults={
                "duration": relativedelta(years=1),
                "cost": 999.99,
                "invoice_reference": "AMS Membership",
                "archived": False,
                "description": (
                    "Annual organisation membership with unlimited seats for your "
                    "entire team. Great for larger schools."
                ),
            },
        )
        MembershipOption.objects.update_or_create(
            name="Sample Organisation Membership - 1 Year (Max 5 seats)",
            type=MembershipOptionType.ORGANISATION,
            defaults={
                "duration": relativedelta(years=1),
                "cost": 599.99,
                "invoice_reference": "AMS Membership",
                "max_seats": 5,
                "archived": False,
                "description": "Ideal for small teams with up to 5 members.",
            },
        )

        self.stdout.write("✅ Membership options updated.\n")
