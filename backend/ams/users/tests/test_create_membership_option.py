from decimal import Decimal
from typing import Any, Dict

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.test import TestCase

from ..forms import MembershipOptionForm
from ..models import MembershipOption, MembershipOptionType


class CreateMembershipOptionTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="testadminuser", is_staff=True)

        self.form_values: Dict[str, Any] = {
            "name": "Name",
            "type": MembershipOptionType.INDIVIDUAL,
            "duration_0": "10",
            "duration_1": "days",
            "cost": "123.45",
        }

        self.url = "/users/membership-options/create/"
        self.client.force_login(self.user)

    def test_should_require_logged_in_user(self) -> None:
        # Given
        self.client.logout()

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"/users/login/?next={self.url}", response.url)

    def test_should_not_allow_access_to_non_admin_user(self) -> None:
        # Given
        self.user.is_staff = False
        self.user.save()

        self.client.force_login(self.user)

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(401, response.status_code)

    def test_post_incomplete_form_to_endpoint(self) -> None:
        # When
        response = self.client.post(self.url, {})

        # Then
        self.assertEqual(200, response.status_code)
        self.assertFormError(response, "form", "name", "This field is required.")
        self.assertFormError(response, "form", "type", "This field is required.")
        self.assertFormError(response, "form", "duration", "This field is required.")
        self.assertFormError(response, "form", "cost", "This field is required.")
        self.assertTemplateUsed(response, "edit_membership_option.html")

    def test_should_create_membership_option(self) -> None:
        # When
        response = self.client.post(self.url, self.form_values)

        # Then
        self.assertEqual(302, response.status_code)

        membership_option = MembershipOption.objects.get(name=self.form_values["name"])

        self.assertEqual(membership_option.name, self.form_values["name"])
        self.assertEqual(membership_option.type, self.form_values["type"])
        self.assertEqual(membership_option.duration, relativedelta(days=int(self.form_values["duration_0"])))
        self.assertEqual(membership_option.cost, Decimal(self.form_values["cost"]))

    def test_should_show_membership_option_created_message(self) -> None:
        # When
        response = self.client.post(self.url, self.form_values)

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual("/users/membership-options/?membership_option_created=true", response.url)

        response = self.client.get(response.url)

        expected_messages = [{"value": "Membership Option Added", "type": "success"}]
        self.assertEqual(expected_messages, response.context.get("show_messages"))

    def test_submitting_blank_form_should_return_expected_errors(self) -> None:
        # Given
        form = MembershipOptionForm(data={})

        # When
        form_valid = form.is_valid()

        # Then
        expected_errors = {
            "name": ["This field is required."],
            "type": ["This field is required."],
            "duration": ["This field is required."],
            "cost": ["This field is required."],
        }

        self.assertEqual(form_valid, False)
        self.assertDictEqual(expected_errors, form.errors)

    def test_completed_form_is_valid(self) -> None:
        # Given
        form = MembershipOptionForm(data=self.form_values)

        # When
        form_valid = form.is_valid()

        # Then
        expected_errors: Dict[str, Any] = {}

        self.assertEqual(form_valid, True)
        self.assertDictEqual(expected_errors, form.errors)
