from io import StringIO
from tempfile import NamedTemporaryFile
from typing import Any, Dict

import pytest
from dateutil.tz import gettz
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from django.utils.formats import date_format

from ams.test.utils import (
    any_membership_option,
    any_organisation,
    any_organisation_type,
)
from ams.users.models import MembershipOptionType, Organisation

if "ams.dtta" not in settings.INSTALLED_APPS:
    pytest.skip(reason="ams.dtta not in INSTALLED_APPS", allow_module_level=True)


class UserImportTests(TestCase):
    def setUp(self) -> None:
        self.header = ",".join(
            [
                "Id",
                "Joining Date",
                "First Name",
                "Last Name",
                "Email",
                "Organisation",
                "Individual Type",
                "Organisation type",
                "Join Date",
                "Admin for organisation",
            ]
        )

        self.time_zone = gettz(settings.TIME_ZONE)
        self.individual_membership_option = any_membership_option(type=MembershipOptionType.INDIVIDUAL)

        self.organisation_type = any_organisation_type()
        self.organisation_membership_option = any_membership_option(
            name=self.organisation_type.name, type=MembershipOptionType.ORGANISATION
        )

    def _call_import_users_command(self, csv_content: str, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        stdout = StringIO()
        stderr = StringIO()

        with NamedTemporaryFile(suffix=".csv") as file_pointer:
            file_pointer.write(csv_content.encode("utf-8"))
            file_pointer.flush()

            call_command(
                "importdttausers",
                file_pointer.name,
                stdout=stdout,
                stderr=stderr,
                **kwargs,
            )

        return {"stdout": stdout.getvalue(), "stderr": stderr.getvalue()}

    def test_should_not_create_users_in_dry_run_mode(self) -> None:
        # Given
        email = "smith@example.com"
        csv_content = f"""{self.header}
1,01/01/2000,John,Smith,{email},,{self.individual_membership_option.name},,01/01/2010,
"""

        # When
        result = self._call_import_users_command(csv_content, dry_run=True)
        self.assertEqual(result["stderr"], "")

        # Then
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(email=email)

    def test_should_create_expected_user_with_individual_membership(self) -> None:
        # Given
        email = "smith@example.com"
        first_name = "John"
        last_name = "Smith"
        join_date = "01/01/2010"

        csv_content = f"""{self.header}
1,01/01/2000,{first_name},{last_name},{email},,{self.individual_membership_option.name},,{join_date},
"""

        # When
        result = self._call_import_users_command(csv_content)
        self.assertEqual(result["stderr"], "")

        # Then
        user = User.objects.get(email=email)
        with self.subTest("Creates expected user"):
            self.assertEqual(user.username, email)
            self.assertEqual(user.first_name, first_name)
            self.assertEqual(user.last_name, last_name)
            self.assertEqual(
                date_format(user.date_joined.astimezone(self.time_zone), format=settings.SHORT_DATE_FORMAT), join_date
            )
            self.assertEqual(user.is_active, False)
            self.assertEqual(user.is_staff, False)
            self.assertEqual(user.is_superuser, False)

        with self.subTest("Creates expected individual user membership"):
            user_membership = user.user_memberships.get()
            self.assertEqual(user_membership.membership_option, self.individual_membership_option)
            self.assertEqual(user_membership.start_date, timezone.localdate())
            self.assertEqual(user_membership.created_datetime.astimezone(self.time_zone).date(), timezone.localdate())
            self.assertEqual(user_membership.invoice, None)

    def test_should_create_expected_user_with_organisation_membership(self) -> None:
        # Given
        old_id = "123"
        email = "smith@example.com"
        first_name = "John"
        last_name = "Smith"
        join_date = "01/01/2010"
        organisation_name = "Organisation name"

        csv_content = f"""{self.header}
{old_id},01/01/2000,{first_name},{last_name},{email},{organisation_name},,{self.organisation_type.name},{join_date},
"""

        # When
        result = self._call_import_users_command(csv_content)
        self.assertEqual(result["stderr"], "")

        # Then
        user = User.objects.get(email=email)
        with self.subTest("Creates expected user"):
            self.assertEqual(user.username, email)
            self.assertEqual(user.first_name, first_name)
            self.assertEqual(user.last_name, last_name)
            self.assertEqual(
                date_format(user.date_joined.astimezone(self.time_zone), format=settings.SHORT_DATE_FORMAT), join_date
            )
            self.assertEqual(user.is_active, False)
            self.assertEqual(user.is_staff, False)
            self.assertEqual(user.is_superuser, False)

        organisation = Organisation.objects.get()
        with self.subTest("Creates expected organisation"):
            self.assertEqual(organisation.name, organisation_name)
            self.assertEqual(organisation.type, self.organisation_type)
            self.assertEqual(organisation.email, f"dtta-default-address+{old_id}@catalyst.net.nz")
            self.assertEqual(organisation.telephone, "N/A")
            self.assertEqual(organisation.contact_name, "N/A")
            self.assertEqual(organisation.postal_address, "N/A")
            self.assertEqual(organisation.postal_suburb, "N/A")
            self.assertEqual(organisation.postal_city, "N/A")
            self.assertEqual(organisation.postal_code, "N/A")

        with self.subTest("Creates expected organisation membership"):
            organisation_membership = organisation.organisation_memberships.get()
            self.assertEqual(organisation_membership.membership_option, self.organisation_membership_option)
            self.assertEqual(organisation_membership.start_date, timezone.localdate())
            self.assertEqual(
                organisation_membership.created_datetime.astimezone(self.time_zone).date(), timezone.localdate()
            )
            self.assertEqual(organisation_membership.invoice, None)

        with self.subTest("Creates expected organisation member"):
            organisation_member = user.organisation_members.get()
            self.assertEqual(organisation_member.organisation, organisation)
            self.assertEqual(
                organisation_member.created_datetime.astimezone(self.time_zone).date(), timezone.localdate()
            )
            self.assertEqual(
                organisation_member.accepted_datetime.astimezone(self.time_zone).date(), timezone.localdate()
            )
            self.assertEqual(organisation_member.is_admin, False)
            self.assertEqual(organisation_member.invite_token, None)

    def test_should_create_organisation_admin_user(self) -> None:
        # Given
        email = "smith@example.com"
        is_organisation_admin = "Y"

        organisation = any_organisation(organisation_type=self.organisation_type)

        csv_content = f"""{self.header}
1,01/01/2000,John,Smith,{email},{organisation.name},,{organisation.type.name},01/01/2010,{is_organisation_admin}
"""

        # When
        result = self._call_import_users_command(csv_content)
        self.assertEqual(result["stderr"], "")

        # Then
        user = User.objects.get(email=email)

        organisation_member = user.organisation_members.get()
        self.assertEqual(organisation_member.organisation, organisation)
        self.assertEqual(organisation_member.is_admin, True)

    def test_should_create_expected_user_organisation_member_with_existing_organisation(self) -> None:
        # Given
        email = "smith@example.com"
        organisation = any_organisation(organisation_type=self.organisation_type)

        csv_content = f"""{self.header}
1,01/01/2000,John,Smith,{email},{organisation.name},,{self.organisation_type.name},01/01/2010,
"""

        # When
        result = self._call_import_users_command(csv_content)
        self.assertEqual(result["stderr"], "")

        # Then
        user = User.objects.get(email=email)
        with self.subTest("Creates expected organisation member"):
            organisation_member = user.organisation_members.get()
            self.assertEqual(organisation_member.organisation, organisation)
            self.assertEqual(
                organisation_member.created_datetime.astimezone(self.time_zone).date(), timezone.localdate()
            )
            self.assertEqual(
                organisation_member.accepted_datetime.astimezone(self.time_zone).date(), timezone.localdate()
            )
            self.assertEqual(organisation_member.is_admin, False)
            self.assertEqual(organisation_member.invite_token, None)

    def test_should_output_error_if_user_with_email_already_exists(self) -> None:
        # Given
        email = "smith@example.com"
        User.objects.create(username=email, email=email, is_active=False)

        csv_content = f"""{self.header}
1,01/01/2000,John,Smith,{email},,{self.individual_membership_option.name},,01/01/2010,
"""

        # When
        result = self._call_import_users_command(csv_content)

        # Then
        self.assertEqual(result["stderr"], f"Skipping line 2 due to error: User with email '{email}' already exists\n")

    def test_should_output_error_if_no_join_date(self) -> None:
        # Given
        join_date = ""
        csv_content = f"""{self.header}
1,01/01/2000,John,Smith,smith@example.com,,{self.individual_membership_option.name},,{join_date},
"""

        # When
        result = self._call_import_users_command(csv_content)

        # Then
        self.assertEqual(result["stderr"], "Skipping line 2 due to error: No join date\n")

    def test_should_output_error_if_join_date_is_invalid(self) -> None:
        # Given
        join_date = "invalid date"
        csv_content = f"""{self.header}
1,01/01/2000,John,Smith,smith@example.com,,{self.individual_membership_option.name},,{join_date},
"""

        # When
        result = self._call_import_users_command(csv_content)

        # Then
        self.assertEqual(result["stderr"], "Skipping line 2 due to error: Invalid join date format\n")

    def test_should_output_error_if_individual_membership_option_not_found(self) -> None:
        # Given
        individual_membership_option_name = "invalid membership name"
        csv_content = f"""{self.header}
1,01/01/2000,John,Smith,smith@example.com,,{individual_membership_option_name},,01/01/2010,
"""

        # When
        result = self._call_import_users_command(csv_content)

        # Then
        self.assertEqual(
            result["stderr"],
            "Skipping line 2 due to error: Individual membership option "
            f"'{individual_membership_option_name}' not found\n",
        )

    def test_should_output_error_if_organisation_membership_option_not_found(self) -> None:
        # Given
        organisation_membership_option_name = "invalid organisation membership name"
        any_organisation_type(name=organisation_membership_option_name)

        csv_content = f"""{self.header}
1,01/01/2000,John,Smith,smith@example.com,New organisation,,{organisation_membership_option_name},01/01/2010,
"""

        # When
        result = self._call_import_users_command(csv_content)

        # Then
        self.assertEqual(
            result["stderr"],
            "Skipping line 2 due to error: Organisation membership option "
            f"'{organisation_membership_option_name}' not found\n",
        )

    def test_should_output_error_if_organisation_type_not_found(self) -> None:
        # Given
        organisation_type_name = "invalid organisation type"
        csv_content = f"""{self.header}
1,01/01/2000,John,Smith,smith@example.com,New organisation,,{organisation_type_name},01/01/2010,
"""

        # When
        result = self._call_import_users_command(csv_content)

        # Then
        self.assertEqual(
            result["stderr"], f"Skipping line 2 due to error: Organisation type '{organisation_type_name}' not found\n"
        )

    def test_should_output_error_if_no_individual_or_organisation_membership_details(self) -> None:
        # Given
        csv_content = f"""{self.header}
1,01/01/2000,John,Smith,smith@example.com,,,,01/01/2010,
"""

        # When
        result = self._call_import_users_command(csv_content)

        # Then
        self.assertEqual(
            result["stderr"], "Skipping line 2 due to error: No individual or organisation membership details\n"
        )
