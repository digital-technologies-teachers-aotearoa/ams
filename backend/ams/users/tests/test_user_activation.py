from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.core import mail
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone
from registration.models import RegistrationProfile

from ams.test.utils import any_user_account

from ..models import MembershipOption, MembershipOptionType, UserMembership


class UserActivationTests(TestCase):
    def setUp(self) -> None:
        request = RequestFactory().get("/")

        self.user = RegistrationProfile.objects.create_inactive_user(
            get_current_site(request),
            send_email=False,
            username="user@example.com",
            email="user@example.com",
            first_name="John",
            last_name="Smith",
            password="valid password",
        )
        any_user_account(user=self.user)

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

    def test_valid_activation_for_user_with_user_membership_sends_notification_email_to_staff(self) -> None:
        # Given
        activation_key = self.registration_profile.activation_key

        membership_option = MembershipOption.objects.create(
            name="Membership Option", type=MembershipOptionType.INDIVIDUAL, duration="P1M", cost="1.00"
        )
        UserMembership.objects.create(
            user=self.user,
            membership_option=membership_option,
            created_datetime=timezone.localtime(),
            start_date=timezone.localtime().date(),
        )

        User.objects.create_user(
            first_name="Inactive Staff",
            username="inactive_staff",
            is_staff=True,
            is_active=False,
            email="user@example.com",
        )

        User.objects.create_user(
            first_name="Not Staff", username="not_staff", is_staff=False, is_active=True, email="user@example.com"
        )

        staff_user = User.objects.create_user(
            first_name="John", username="staff", is_staff=True, is_active=True, email="user@example.com"
        )

        site = Site.objects.get()

        # When
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.get(f"/users/activate/{activation_key}/")

        # Then
        self.assertEqual(200, response.status_code)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "New user registration")

        self.assertEqual(
            mail.outbox[0].body,
            f"""Hello {staff_user.first_name},

A new user has registered for {site.name} and needs approval.

Click the link below to review the user and approve their membership.

https://{site.domain}/users/view/{self.user.id}
""",
        )

    @override_settings(BILLING_SERVICE_CLASS="ams.billing.service.MockBillingService")
    def test_valid_activation_for_user_with_user_membership_creates_invoice(self) -> None:
        # Given
        activation_key = self.registration_profile.activation_key

        membership_option = MembershipOption.objects.create(
            name="Membership Option", type=MembershipOptionType.INDIVIDUAL, duration="P1M", cost="1.00"
        )
        user_membership = UserMembership.objects.create(
            user=self.user,
            membership_option=membership_option,
            created_datetime=timezone.localtime(),
            start_date=timezone.localtime().date(),
        )

        # When
        response = self.client.get(f"/users/activate/{activation_key}/")
        self.assertEqual(200, response.status_code)

        # Then
        user_membership.refresh_from_db()
        invoice = user_membership.invoice

        self.assertIsNotNone(invoice)
        self.assertEqual(invoice.amount, Decimal(membership_option.cost))

    @override_settings(BILLING_SERVICE_CLASS="ams.billing.service.MockBillingService")
    @patch("ams.billing.service.MockBillingService.create_invoice")
    def test_billing_service_error_during_activation_does_not_activate_user(self, mock_create_invoice: Mock) -> None:
        # Given
        mock_create_invoice.side_effect = Exception("any exception")

        activation_key = self.registration_profile.activation_key

        membership_option = MembershipOption.objects.create(
            name="Membership Option", type=MembershipOptionType.INDIVIDUAL, duration="P1M", cost="1.00"
        )
        UserMembership.objects.create(
            user=self.user,
            membership_option=membership_option,
            created_datetime=timezone.localtime(),
            start_date=timezone.localtime().date(),
        )

        # When
        response = self.client.get(f"/users/activate/{activation_key}/")

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(response.url, "/users/activation-error/")

        with self.subTest("Has expected error message"):
            response = self.client.get(response.url)
            self.assertEqual(200, response.status_code)

            expected_messages = [
                {
                    "value": (
                        "Your email could not be verified at this time. "
                        "Please try again in a few minutes by visiting the link provided in your email. "
                        "If this message reappears please contact the site administrator."
                    ),
                    "type": "error",
                }
            ]
            self.assertEqual(expected_messages, response.context.get("show_messages"))

        with self.subTest("User is not made active"):
            self.user.refresh_from_db()
            self.assertEqual(self.user.is_active, False)

        with self.subTest("Registration profile is not activated"):
            self.registration_profile.refresh_from_db()
            self.assertEqual(self.registration_profile.activated, False)

    def test_valid_activation_for_user_without_user_membership_does_not_notify_staff(self) -> None:
        # Given
        activation_key = self.registration_profile.activation_key

        User.objects.create_user(
            first_name="Inactive Staff",
            username="inactive_staff",
            is_staff=True,
            is_active=False,
            email="user@example.com",
        )

        User.objects.create_user(
            first_name="Not Staff", username="not_staff", is_staff=False, is_active=True, email="user@example.com"
        )

        User.objects.create_user(
            first_name="John", username="staff", is_staff=True, is_active=True, email="user@example.com"
        )

        # When
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.get(f"/users/activate/{activation_key}/")

        # Then
        self.assertEqual(200, response.status_code)
        self.assertEqual(len(mail.outbox), 0)

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
