from django.contrib.sites.requests import RequestSite
from django.test import RequestFactory, TestCase
from registration.models import RegistrationProfile


class UserActivationTests(TestCase):
    def setUp(self) -> None:
        request = RequestFactory().get("/")

        self.user = RegistrationProfile.objects.create_inactive_user(
            RequestSite(request),
            send_email=False,
            username="user@example.com",
            email="user@example.com",
            first_name="John",
            last_name="Smith",
            password="valid password",
        )

        self.registration_profile = RegistrationProfile.objects.get()

    def test_valid_activation_key_makes_user_active(self) -> None:
        # Given
        activation_key = self.registration_profile.activation_key

        # When
        response = self.client.get(f"/users/activate/{activation_key}/")

        # Then
        self.user.refresh_from_db()

        self.assertEqual(200, response.status_code)
        self.assertEqual(True, self.user.is_active)
        self.assertTemplateUsed(response, "base/email_confirmation_page.html")

    def test_reusing_activation_key_with_active_user_redirects_to_home_page(self) -> None:
        # Given
        activation_key = self.registration_profile.activation_key
        self.registration_profile.activated = True
        self.registration_profile.save()

        self.user.is_active = True
        self.user.save()

        # When
        response = self.client.get(f"/users/activate/{activation_key}/")

        # Then
        self.user.refresh_from_db()

        self.assertEqual(302, response.status_code)
        self.assertEqual(response.url, "/")
        self.assertEqual(True, self.user.is_active)

    def test_invalid_activation_key_returns_unauthorized_response(self) -> None:
        # Given
        activation_key = "invalid"

        # When
        response = self.client.get(f"/users/activate/{activation_key}/")

        # Then
        self.user.refresh_from_db()

        self.assertEqual(401, response.status_code)
        self.assertEqual(False, self.user.is_active)
