import csv
from datetime import datetime
from typing import Any, List

from dateutil.tz import gettz
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
from django.utils import timezone

from ams.billing.models import Account
from ams.users.models import (
    MembershipOption,
    MembershipOptionType,
    Organisation,
    OrganisationMember,
    OrganisationMembership,
    OrganisationType,
    UserMembership,
)


class UserImportException(Exception):
    pass


class Command(BaseCommand):
    help = "Import users from CSV file."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("filename", help="User CSV file to import")
        parser.add_argument("--dry-run", action="store_true", help="Validate file without creating any users")

    def validate_row(self, row: List[str]) -> None:
        (
            _old_id,
            _unused,
            _first_name,
            _last_name,
            email,
            organisation_name,
            individual_type_name,
            organisation_type_name,
            join_date,
            _organisation_admin,
        ) = row

        if User.objects.filter(email=email).exists():
            raise UserImportException(f"User with email '{email}' already exists")

        if not join_date:
            raise UserImportException("No join date")

        try:
            datetime.strptime(join_date, settings.DATE_INPUT_FORMATS[-1])
        except ValueError:
            raise UserImportException("Invalid join date format")

        if not individual_type_name and not (organisation_name and organisation_type_name):
            raise UserImportException("No individual or organisation membership details")

        if individual_type_name:
            if not MembershipOption.objects.filter(
                name=individual_type_name, type=MembershipOptionType.INDIVIDUAL
            ).exists():
                raise UserImportException(f"Individual membership option '{individual_type_name}' not found")

        if organisation_name and organisation_type_name:
            if not OrganisationType.objects.filter(name=organisation_type_name).exists():
                raise UserImportException(f"Organisation type '{organisation_type_name}' not found")

            if not MembershipOption.objects.filter(
                name=organisation_type_name, type=MembershipOptionType.ORGANISATION
            ).exists():
                raise UserImportException(f"Organisation membership option '{organisation_type_name}' not found")

    def import_user(self, row: List[str]) -> None:
        (
            old_id,
            _unused,
            first_name,
            last_name,
            email,
            organisation_name,
            individual_type_name,
            organisation_type_name,
            join_date,
            organisation_admin,
        ) = row
        self.validate_row(row)

        # Create user
        date_joined = datetime.strptime(join_date, settings.DATE_INPUT_FORMATS[-1]).astimezone(
            gettz(settings.TIME_ZONE)
        )
        new_user = User.objects.create(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            date_joined=date_joined,
            is_active=False,
        )
        Account.objects.create(user=new_user)

        if individual_type_name:
            user_membership_option = MembershipOption.objects.get(
                name=individual_type_name, type=MembershipOptionType.INDIVIDUAL
            )
            UserMembership.objects.create(
                user=new_user,
                membership_option=user_membership_option,
                start_date=timezone.localdate(),
                created_datetime=timezone.localtime(),
                invoice=None,
            )

        elif organisation_name:
            organisation = Organisation.objects.filter(name=organisation_name).first()
            if not organisation:
                organisation_email = f"dtta-default-address+{old_id}@catalyst.net.nz"
                organisation_type = OrganisationType.objects.get(name=organisation_type_name)
                placeholder = "N/A"
                organisation = Organisation.objects.create(
                    name=organisation_name,
                    type=organisation_type,
                    email=organisation_email,
                    telephone=placeholder,
                    contact_name=placeholder,
                    postal_address=placeholder,
                    postal_suburb=placeholder,
                    postal_city=placeholder,
                    postal_code=placeholder,
                )
                organisation_membership_option = MembershipOption.objects.get(
                    name=organisation_type_name, type=MembershipOptionType.ORGANISATION
                )
                OrganisationMembership.objects.create(
                    organisation=organisation,
                    membership_option=organisation_membership_option,
                    start_date=timezone.localdate(),
                    created_datetime=timezone.localtime(),
                    invoice=None,
                )

            is_organisation_admin = False
            if "Y" in organisation_admin:
                is_organisation_admin = True

            OrganisationMember.objects.create(
                user=new_user,
                organisation=organisation,
                created_datetime=timezone.localtime(),
                accepted_datetime=timezone.localtime(),
                is_admin=is_organisation_admin,
                invite_token=None,
            )

    def handle(self, *args: Any, **options: Any) -> None:
        filename: str = options["filename"]
        dry_run: bool = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.MIGRATE_HEADING("Checking file"))
        else:
            self.stdout.write(self.style.MIGRATE_HEADING("Importing users"))

        with transaction.atomic():
            with open(filename, newline="") as csv_file:
                csv_reader = csv.reader(csv_file)
                line_number = 0
                for row in csv_reader:
                    line_number += 1

                    # Skip header
                    if line_number == 1:
                        continue

                    try:
                        if dry_run:
                            self.validate_row(row)
                        else:
                            self.import_user(row)
                    except UserImportException as e:
                        # NOTE: Skip entries that can't be imported and continue
                        self.stderr.write(f"Skipping line {line_number} due to error: {e}")

        self.stdout.write(self.style.SUCCESS("Done"))
