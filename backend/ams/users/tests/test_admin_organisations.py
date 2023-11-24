from django.contrib.auth.models import User
from django.test import TestCase

from ..models import Organisation, OrganisationType


class AdminOrganisationListTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="testadminuser", is_staff=True)

        organisation_type = OrganisationType.objects.create(name="Secondary School")

        self.organisation = Organisation.objects.create(
            name="Some School",
            type=organisation_type,
            postal_address="123 Main Street\nCapital City",
            telephone="555-12345",
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

        expected_columns = ["name", "type", "postal_address", "telephone", "actions"]
        columns = [column.name for column in response.context["table"].columns]
        self.assertListEqual(expected_columns, columns)

    def test_should_show_expected_headings(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_columns = ["Name", "Type", "Postal Address", "Office Phone", "Actions"]
        columns = [column.header for column in response.context["table"].columns]
        self.assertListEqual(expected_columns, columns)

    def test_should_show_expected_rows(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        rows = []
        for row in response.context["table"].rows:
            rows.append([cell for cell in row.cells])

        expected_rows = [
            [
                self.organisation.name,
                self.organisation.type.name,
                self.organisation.postal_address,
                self.organisation.telephone,
                "",
            ]
        ]

        self.assertListEqual(expected_rows, rows)
