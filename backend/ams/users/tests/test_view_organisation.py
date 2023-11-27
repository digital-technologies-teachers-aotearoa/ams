from django.contrib.auth.models import User
from django.test import TestCase

from ..models import Organisation, OrganisationType


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

        self.user = User.objects.create_user(username="testadminuser", is_staff=True)
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
