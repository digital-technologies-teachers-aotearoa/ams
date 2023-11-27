from django.contrib.auth.models import User
from django.test import TestCase

from ...test.utils import parse_response_table_rows
from ..models import Organisation, OrganisationType


class AdminOrganisationListTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="testadminuser", is_staff=True)

        organisation_type = OrganisationType.objects.create(name="Secondary School")

        self.organisation = Organisation.objects.create(
            name="Some School",
            type=organisation_type,
            telephone="555-12345",
            email="john@example.com",
            contact_name="John Smith",
            street_address="123 Main Street",
            city="Capital City",
            postal_code="8080",
        )

        self.url = "/users/organisations/"

        self.client.force_login(self.user)

    def test_should_not_allow_access_to_non_admin_user(self) -> None:
        # Given
        self.user.is_staff = False
        self.user.save()

        self.client.force_login(self.user)

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(403, response.status_code)

    def test_should_use_expected_templates(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "admin_organisations.html")
        self.assertTemplateUsed(response, "admin_organisation_actions.html")

    def test_should_show_expected_columns(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_columns = ["name", "type", "telephone", "email", "contact_name", "city", "actions"]
        columns = [column.name for column in response.context["table"].columns]
        self.assertListEqual(expected_columns, columns)

    def test_should_show_expected_headings(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_columns = ["Name", "Type", "Telephone", "Email", "Contact Name", "City", "Actions"]
        columns = [column.header for column in response.context["table"].columns]
        self.assertListEqual(expected_columns, columns)

    def test_should_show_expected_rows(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        rows = parse_response_table_rows(response)

        expected_rows = [
            [
                self.organisation.name,
                self.organisation.type.name,
                self.organisation.telephone,
                self.organisation.email,
                self.organisation.contact_name,
                self.organisation.city,
                "View,Edit",
            ]
        ]

        self.assertListEqual(expected_rows, rows)
