from typing import Any, Dict

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from registration.models import RegistrationProfile

from ..forms import IndividualRegistrationForm
from ..models import MembershipOption, MembershipOptionType


class IndividualRegistrationFormTests(TestCase):
    def setUp(self) -> None:
        MembershipOption.objects.create(
            name="Primary School", type=MembershipOptionType.INDIVIDUAL, duration="P6M", cost="10.00"
        )
        MembershipOption.objects.create(
            name="Secondary School", type=MembershipOptionType.INDIVIDUAL, duration="P1Y", cost="20.00"
        )
        MembershipOption.objects.create(
            name="Club", type=MembershipOptionType.ORGANISATION, duration="P1Y", cost="50.00"
        )

        self.form_values = {
            "email": "user@example.com",
            "confirm_email": "user@example.com",
            "first_name": "John",
            "last_name": "Smith",
            "password": "valid password",
            "confirm_password": "valid password",
            "membership_option": "Primary School",
        }

    def test_get_endpoint(self) -> None:
        # When
        response = self.client.get("/users/individual-registration/")

        # Then
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "individual_registration.html")

    def test_post_incomplete_form_to_endpoint(self) -> None:
        # When
        response = self.client.post("/users/individual-registration/", {})

        # Then
        self.assertEqual(200, response.status_code)
        self.assertFormError(response, "form", "email", "This field is required.")
        self.assertTemplateUsed(response, "individual_registration.html")

    def test_post_completed_form_to_endpoint_creates_expected_user(self) -> None:
        # When
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post("/users/individual-registration/", self.form_values)

        # Then
        self.assertEqual(201, response.status_code)
        self.assertTemplateUsed(response, "individual_registration_pending.html")

        user = User.objects.get(username=self.form_values["email"])

        with self.subTest("created expected user"):
            self.assertEqual(user.email, self.form_values["email"])
            self.assertEqual(user.first_name, self.form_values["first_name"])
            self.assertEqual(user.last_name, self.form_values["last_name"])
            self.assertEqual(user.is_active, False)

        user_membership = user.user_memberships.first()

        with self.subTest("created expected user membership"):
            self.assertEqual(user_membership.membership_option.name, self.form_values["membership_option"])
            self.assertIsNone(user_membership.approved_datetime)

        with self.subTest("verification email sent"):
            activation_key = RegistrationProfile.objects.get(user=user).activation_key

            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, "Account activation on testserver")
            self.maxDiff = None
            self.assertEqual(
                mail.outbox[0].body,
                f"""Hello {user.first_name},

You're almost ready to start enjoying testserver.

Simply click the link below to verify your email address.

https://testserver/users/activate/{activation_key}/
""",
            )

    def test_blank_form_should_include_expected_values(self) -> None:
        # Given
        form = IndividualRegistrationForm()

        # When
        choices = list(form.fields["membership_option"].choices)

        # Then
        expected_choices = [
            ("Primary School", "$10.00 for 6 months"),
            ("Secondary School", "$20.00 for 1 year"),
        ]
        self.assertListEqual(expected_choices, choices)

    def test_submitting_blank_form_should_return_expected_errors(self) -> None:
        # Given
        form = IndividualRegistrationForm(data={})

        # When
        form_valid = form.is_valid()

        # Then
        expected_errors = {
            "email": ["This field is required."],
            "confirm_email": ["This field is required."],
            "first_name": ["This field is required."],
            "last_name": ["This field is required."],
            "password": ["This field is required."],
            "confirm_password": ["This field is required."],
            "membership_option": ["This field is required."],
        }

        self.assertEqual(form_valid, False)
        self.assertDictEqual(expected_errors, form.errors)

    def test_completed_form_is_valid(self) -> None:
        # Given
        form = IndividualRegistrationForm(data=self.form_values)

        # When
        form_valid = form.is_valid()

        # Then
        expected_errors: Dict[str, Any] = {}

        self.assertEqual(form_valid, True)
        self.assertDictEqual(expected_errors, form.errors)

    def test_username_with_email_does_not_exist(self) -> None:
        # Given
        User.objects.create_user(
            username=self.form_values["email"], email=self.form_values["email"], password=self.form_values["password"]
        )

        form = IndividualRegistrationForm(data=self.form_values)

        # When
        form_valid = form.is_valid()

        # Then
        expected_errors = {
            "email": ["A user with this email address already exists."],
        }

        self.assertEqual(form_valid, False)
        self.assertDictEqual(expected_errors, form.errors)

    def test_should_check_email_is_valid(self) -> None:
        invalid_email = "invalid email"

        form = IndividualRegistrationForm(
            data={**self.form_values, "email": invalid_email, "confirm_email": invalid_email}
        )

        # When
        form_valid = form.is_valid()

        # Then
        expected_errors = {
            "email": ["Enter a valid email address."],
        }

        self.assertEqual(form_valid, False)
        self.assertDictEqual(expected_errors, form.errors)

    def test_should_check_password_is_valid(self) -> None:
        invalid_password = "invalid"

        form = IndividualRegistrationForm(
            data={**self.form_values, "password": invalid_password, "confirm_password": invalid_password}
        )

        # When
        form_valid = form.is_valid()

        # Then
        expected_errors = {
            "password": ["This password is too short. It must contain at least 8 characters."],
        }

        self.assertEqual(form_valid, False)
        self.assertDictEqual(expected_errors, form.errors)

    def test_should_check_confirm_email_matches(self) -> None:
        # Given
        form = IndividualRegistrationForm(data={**self.form_values, "confirm_email": "different-user@example.com"})

        # When
        form_valid = form.is_valid()

        expected_errors = {
            "confirm_email": ["The two email fields didn't match."],
        }

        self.assertEqual(form_valid, False)
        self.assertDictEqual(expected_errors, form.errors)

    def test_should_check_confirm_password_matches(self) -> None:
        # Given
        form = IndividualRegistrationForm(data={**self.form_values, "confirm_password": "different password"})

        # When
        form_valid = form.is_valid()

        expected_errors = {
            "confirm_password": ["The two password fields didn't match."],
        }

        self.assertEqual(form_valid, False)
        self.assertDictEqual(expected_errors, form.errors)
