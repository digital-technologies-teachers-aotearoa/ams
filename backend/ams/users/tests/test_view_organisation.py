from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from django.utils.formats import date_format

from ...test.utils import parse_response_table_rows
from ..models import Organisation, OrganisationMember, OrganisationType


class ViewOrganisationFormTests(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(
            type=OrganisationType.objects.create(name="Primary School"),
            name="Any Organisation",
            telephone="555-12345",
            contact_name="John Smith",
            email="john@example.com",
            street_address="123 Main Street",
            suburb="",
            city="Capital City",
            postal_code="8080",
            postal_address="PO BOX 1234\nCapital City 8082",
        )

        self.user = User.objects.create_user(
            username="testadminuser", email="user@example.com", first_name="John", last_name="Smith", is_staff=True
        )

        self.organisation_member = OrganisationMember.objects.create(
            user=self.user,
            organisation=self.organisation,
            invite_email=self.user.email,
            invite_token="token",
            created_datetime=timezone.localtime(),
            accepted_datetime=timezone.localtime(),
        )

        self.client.force_login(self.user)

        self.url = f"/users/organisations/view/{self.organisation.pk}/"

    def test_should_not_allow_access_to_non_admin_user(self) -> None:
        # Given
        self.user.is_staff = False
        self.user.save()

        self.client.force_login(self.user)

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(403, response.status_code)

    def test_get_endpoint(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "organisation_view.html")

    def test_should_show_expected_members_columns(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_membership_columns = ["name", "email", "status", "join_date", "actions"]
        columns = [column.name for column in response.context["table"].columns]
        self.assertListEqual(expected_membership_columns, columns)

    def test_should_show_expected_members_headings(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_membership_headings = ["Name", "Email", "Status", "Join Date", "Actions"]
        headings = [column.header for column in response.context["table"].columns]
        self.assertListEqual(expected_membership_headings, headings)

    def test_should_show_expected_organisation_members(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        rows = parse_response_table_rows(response)

        expected_rows = [
            [
                self.organisation_member.user.get_full_name(),
                self.organisation_member.user.email,
                "Active",
                date_format(
                    timezone.localtime(self.organisation_member.accepted_datetime).date(), format="SHORT_DATE_FORMAT"
                ),
                "",
            ]
        ]

        self.assertListEqual(expected_rows, rows)

    def test_should_show_non_accepted_invite_as_invited(self) -> None:
        # Given
        self.organisation_member.accepted_datetime = None
        self.organisation_member.save()

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        rows = parse_response_table_rows(response)

        expected_rows = [
            [
                self.organisation_member.user.get_full_name(),
                self.organisation_member.user.email,
                "Invited",
                "—",
                "",
            ]
        ]

        self.assertListEqual(expected_rows, rows)
