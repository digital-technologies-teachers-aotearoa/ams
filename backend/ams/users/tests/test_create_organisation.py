from typing import Any, Dict

from django.contrib.auth.models import User
from django.test import TestCase

from ..forms import OrganisationForm
from ..models import Organisation, OrganisationType


class CreateOrganisationFormTests(TestCase):
    def setUp(self) -> None:
        self.organisation_types = [
            OrganisationType.objects.create(name="Primary School"),
            OrganisationType.objects.create(name="Secondary School"),
        ]

        self.form_values = {
            "type": self.organisation_types[0].id,
            "name": "Any Organisation",
            "telephone": "555-12345",
            "contact_name": "John Smith",
            "email": "john@example.com",
            "street_address": "123 Main Street",
            "suburb_name": "",
            "city": "Capital City",
            "postal_code": "8080",
            "postal_address": "PO BOX 1234\nCapital City 8082",
        }

        self.user = User.objects.create_user(username="testadminuser", is_staff=True)
        self.client.force_login(self.user)

        self.url = "/users/organisations/create/"

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
        self.assertTemplateUsed(response, "create_organisation.html")

    def test_post_incomplete_form_to_endpoint(self) -> None:
        # When
        response = self.client.post(self.url, {})

        # Then
        self.assertEqual(200, response.status_code)
        self.assertFormError(response, "form", "name", "This field is required.")
        self.assertTemplateUsed(response, "create_organisation.html")

    def test_post_completed_form_to_endpoint_creates_organisation(self) -> None:
        # When
        response = self.client.post(self.url, self.form_values)

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual("/users/organisations/?organisation_created=true", response.url)

        organisation = Organisation.objects.get(name=self.form_values["name"])

        self.assertEqual(organisation.name, self.form_values["name"])
        self.assertEqual(organisation.type.id, self.form_values["type"])
        self.assertEqual(organisation.postal_address, self.form_values["postal_address"])
        self.assertEqual(organisation.telephone, self.form_values["telephone"])

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

    def test_blank_form_should_include_expected_values(self) -> None:
        # Given
        form = OrganisationForm()

        # When
        choices = [(str(choice[0]), choice[1]) for choice in form.fields["type"].choices]

        # Then
        expected_choices = [
            (str(organisation_type.id), organisation_type.name) for organisation_type in self.organisation_types
        ]
        expected_choices.insert(0, ("", ""))

        self.assertListEqual(expected_choices, choices)

    def test_submitting_blank_form_should_return_expected_errors(self) -> None:
        # Given
        form = OrganisationForm(data={})

        # When
        form_valid = form.is_valid()

        # Then
        expected_errors = {
            "name": ["This field is required."],
            "type": ["This field is required."],
            "telephone": ["This field is required."],
            "email": ["This field is required."],
            "contact_name": ["This field is required."],
            "street_address": ["This field is required."],
            "city": ["This field is required."],
            "postal_code": ["This field is required."],
        }

        self.assertEqual(form_valid, False)
        self.assertDictEqual(expected_errors, form.errors)

    def test_completed_form_is_valid(self) -> None:
        # Given
        form = OrganisationForm(data=self.form_values)

        # When
        form_valid = form.is_valid()

        # Then
        expected_errors: Dict[str, Any] = {}

        self.assertEqual(form_valid, True)
        self.assertDictEqual(expected_errors, form.errors)
