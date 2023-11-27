from typing import Any, Dict

from django.contrib.auth.models import User
from django.test import TestCase

from ..forms import OrganisationForm
from ..models import Organisation, OrganisationType


class EditOrganisationFormTests(TestCase):
    def setUp(self) -> None:
        self.organisation_types = [
            OrganisationType.objects.create(name="Primary School"),
            OrganisationType.objects.create(name="Secondary School"),
        ]

        self.organisation = Organisation.objects.create(
            type=self.organisation_types[0],
            name="Any Organisation",
            telephone="555-12345",
            contact_name="John Smith",
            email="john@example.com",
            street_address="123 Main Street",
            suburb="Some Suburb",
            city="Capital City",
            postal_address="PO BOX 1234",
            postal_suburb="Some Suburb",
            postal_city="Capital City",
            postal_code="8080",
        )

        self.form_values = {
            "type": self.organisation_types[1].id,
            "name": "Other Organisation",
            "telephone": "555-123456",
            "contact_name": "Jane Smith",
            "email": "jane@example.com",
            "street_address": "124 Main Street",
            "suburb": "Other Suburb",
            "city": "Other City",
            "postal_address": "PO BOX 12345",
            "postal_suburb": "Other Suburb",
            "postal_city": "Other City",
            "postal_code": "8081",
        }

        self.user = User.objects.create_user(username="testadminuser", is_staff=True)
        self.client.force_login(self.user)

        self.url = f"/users/organisations/edit/{self.organisation.pk}/"

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
        self.assertTemplateUsed(response, "edit_organisation.html")

    def test_post_incomplete_form_to_endpoint(self) -> None:
        # When
        response = self.client.post(self.url, {})

        # Then
        self.assertEqual(200, response.status_code)
        self.assertFormError(response, "form", "name", "This field is required.")
        self.assertTemplateUsed(response, "edit_organisation.html")

    def test_post_completed_form_to_endpoint_updates_organisation(self) -> None:
        # When
        response = self.client.post(self.url, self.form_values)

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual("/users/organisations/?organisation_updated=true", response.url)

        self.organisation.refresh_from_db()

        self.assertEqual(self.organisation.name, self.form_values["name"])
        self.assertEqual(self.organisation.type.id, self.form_values["type"])
        self.assertEqual(self.organisation.telephone, self.form_values["telephone"])
        self.assertEqual(self.organisation.contact_name, self.form_values["contact_name"])
        self.assertEqual(self.organisation.email, self.form_values["email"])
        self.assertEqual(self.organisation.street_address, self.form_values["street_address"])
        self.assertEqual(self.organisation.suburb, self.form_values["suburb"])
        self.assertEqual(self.organisation.city, self.form_values["city"])
        self.assertEqual(self.organisation.postal_code, self.form_values["postal_code"])
        self.assertEqual(self.organisation.postal_address, self.form_values["postal_address"])

    def test_should_validate_email(self) -> None:
        # Given
        self.form_values["email"] = "invalid"

        # When
        response = self.client.post(self.url, self.form_values)

        # Then
        expected_errors = {
            "email": ["Enter a valid email address."],
        }

        self.assertDictEqual(expected_errors, response.context["form"].errors)

    def test_form_should_include_expected_values(self) -> None:
        # Given
        form = OrganisationForm(instance=self.organisation)

        # When
        choices = [(str(choice[0]), choice[1]) for choice in form.fields["type"].choices]

        # Then
        expected_choices = [
            (str(organisation_type.id), organisation_type.name) for organisation_type in self.organisation_types
        ]
        expected_choices.insert(0, ("", ""))

        self.assertListEqual(expected_choices, choices)

    def test_submitting_empty_form_should_return_expected_errors(self) -> None:
        # Given
        form = OrganisationForm(instance=self.organisation, data={})

        # When
        form_valid = form.is_valid()

        # Then
        expected_errors = {
            "name": ["This field is required."],
            "type": ["This field is required."],
            "telephone": ["This field is required."],
            "email": ["This field is required."],
            "contact_name": ["This field is required."],
            "postal_address": ["This field is required."],
            "postal_city": ["This field is required."],
            "postal_code": ["This field is required."],
        }

        self.assertEqual(form_valid, False)
        self.assertDictEqual(expected_errors, form.errors)

    def test_completed_form_is_valid(self) -> None:
        # Given
        form = OrganisationForm(instance=self.organisation, data=self.form_values)

        # When
        form_valid = form.is_valid()

        # Then
        expected_errors: Dict[str, Any] = {}

        self.assertEqual(form_valid, True)
        self.assertDictEqual(expected_errors, form.errors)
