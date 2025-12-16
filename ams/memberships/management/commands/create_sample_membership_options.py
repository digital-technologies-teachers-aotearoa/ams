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
            },
        )
        MembershipOption.objects.update_or_create(
            name="Sample Organisation Membership - 1 Month",
            type=MembershipOptionType.ORGANISATION,
            defaults={
                "duration": relativedelta(months=1),
                "cost": 99.99,
                "invoice_reference": "AMS Membership",
            },
        )
        MembershipOption.objects.update_or_create(
            name="Sample Organisation Membership - 1 Year",
            type=MembershipOptionType.ORGANISATION,
            defaults={
                "duration": relativedelta(years=1),
                "cost": 999.99,
                "invoice_reference": "AMS Membership",
            },
        )

        self.stdout.write("✅ Membership options updated.\n")
