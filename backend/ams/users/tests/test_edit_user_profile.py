from typing import Any, Dict
from unittest.mock import Mock, patch

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from ams.test.utils import any_user_account

from ..forms import EditUserProfileForm


class EditUserProfileTests(TestCase):
    def setUp(self) -> None:
        self.admin_user = User.objects.create_user(username="testadminuser", is_staff=True)

        self.user = User.objects.create_user(username="testuser", is_staff=False)
        self.user.first_name = "John"
        self.user.last_name = "Smith"
        self.user.email = "user@example.com"
        self.user.save()

        self.account = any_user_account(user=self.user)

        self.form_values = {"first_name": "Firstname", "last_name": "Lastname"}

        self.url = f"/users/edit/{self.user.pk}/"
        self.client.force_login(self.admin_user)

    def test_should_require_logged_in_user(self) -> None:
        # Given
        self.client.logout()

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"/users/login/?next={self.url}", response.url)

    def test_should_allow_admin_user(self) -> None:
        # Given
        self.client.force_login(self.admin_user)

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "edit_user_profile.html")
        self.assertEqual(response.context["user_view_url"], f"/users/view/{self.user.pk}/")

    def test_should_allow_same_user(self) -> None:
        # Given
        self.client.force_login(self.user)

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "edit_user_profile.html")
        self.assertEqual(response.context["user_view_url"], "/users/current/")

    def test_should_not_allow_different_non_admin_user(self) -> None:
        # Given
        other_user = User.objects.create_user(username="otheruser", is_staff=False, is_active=True)
        self.client.force_login(other_user)

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(401, response.status_code)

    def test_post_incomplete_form_to_endpoint(self) -> None:
        # When
        response = self.client.post(self.url, {})

        # Then
        self.assertEqual(200, response.status_code)
        self.assertFormError(response, "form", "first_name", "This field is required.")
        self.assertFormError(response, "form", "last_name", "This field is required.")
        self.assertTemplateUsed(response, "edit_user_profile.html")

    def test_should_update_users_details(self) -> None:
        # When
        response = self.client.post(self.url, self.form_values)

        # Then
        self.assertEqual(302, response.status_code)

        self.user.refresh_from_db()

        self.assertEqual(self.user.first_name, self.form_values["first_name"])
        self.assertEqual(self.user.last_name, self.form_values["last_name"])

    @override_settings(DISCOURSE_API_KEY="API-KEY")
    @patch("pydiscourse.DiscourseClient.sync_sso")
    def test_should_sync_user_profile_update_to_forum(self, mock_sync_sso: Mock) -> None:
        # When
        response = self.client.post(self.url, self.form_values)

        # Then
        self.assertEqual(302, response.status_code)

        self.user.refresh_from_db()

        mock_sync_sso.assert_called_with(
            sso_secret=settings.DISCOURSE_CONNECT_SECRET,
            name=self.user.display_name,
            username=self.user.username,
            email=self.user.email,
            external_id=self.user.id,
            avatar_url=None,
        )

    def test_should_show_profile_updated_message(self) -> None:
        # When
        response = self.client.post(self.url, self.form_values)

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"/users/view/{self.user.pk}/?profile_updated=true", response.url)

        response = self.client.get(response.url)

        expected_messages = [{"value": "Profile Updated", "type": "success"}]
        self.assertEqual(expected_messages, response.context.get("show_messages"))

    def test_should_not_update_username(self) -> None:
        # Given
        username = "newusername"
        old_username = self.user.username

        # When
        response = self.client.post(
            self.url,
            {
                **self.form_values,
                "username": username,
            },
        )

        # Then
        self.assertEqual(302, response.status_code)

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, old_username)

    def test_submitting_blank_form_should_return_expected_errors(self) -> None:
        # Given
        form = EditUserProfileForm(instance=self.user, data={})

        # When
        form_valid = form.is_valid()

        # Then
        expected_errors = {
            "first_name": ["This field is required."],
            "last_name": ["This field is required."],
        }

        self.assertEqual(form_valid, False)
        self.assertDictEqual(expected_errors, form.errors)

    def test_completed_form_is_valid(self) -> None:
        # Given
        form = EditUserProfileForm(instance=self.user, data=self.form_values)

        # When
        form_valid = form.is_valid()

        # Then
        expected_errors: Dict[str, Any] = {}

        self.assertEqual(form_valid, True)
        self.assertDictEqual(expected_errors, form.errors)
