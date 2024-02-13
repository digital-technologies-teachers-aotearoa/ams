from datetime import timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from dateutil.relativedelta import relativedelta
from dateutil.tz import gettz
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from django.utils.formats import date_format

from ams.billing.models import Account
from ams.test.utils import any_membership_option, any_organisation, any_user

from ..models import (
    MembershipOption,
    MembershipOptionType,
    OrganisationMember,
    OrganisationMembership,
)


class AddOrganisationMembershipTests(TestCase):
    def setUp(self) -> None:
        self.admin_user = User.objects.create_user(
            username="testadminuser", first_name="Admin", email="user@example.com", is_staff=True
        )

        self.user = any_user()

        self.time_zone = gettz(settings.TIME_ZONE)

        membership_option = any_membership_option(
            name="First Membership Option", type=MembershipOptionType.ORGANISATION, duration="P1M", cost="1.00"
        )
        any_membership_option(
            name="Second Membership Option", type=MembershipOptionType.ORGANISATION, duration="P2M", cost="2.00"
        )

        start = timezone.localtime() - timedelta(days=7)

        self.organisation = any_organisation()

        self.organisation_member = OrganisationMember.objects.create(
            user=self.user,
            organisation=self.organisation,
            invite_email=self.user.email,
            invite_token="token",
            created_datetime=timezone.localtime(),
            accepted_datetime=timezone.localtime(),
            is_admin=True,
        )

        self.organisation_membership = OrganisationMembership.objects.create(
            organisation=self.organisation,
            membership_option=membership_option,
            created_datetime=start,
            start_date=start.date(),
        )
        Account.objects.create(organisation=self.organisation)

        self.url = f"/users/organisations/add-membership/{self.organisation.pk}/"
        self.client.force_login(self.user)

    def test_should_require_logged_in_user(self) -> None:
        # Given
        self.client.logout()

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"/users/login/?next={self.url}", response.url)

    def test_should_not_allow_other_non_admin_user(self) -> None:
        # Given
        otheruser = User.objects.create_user(username="otheruser", is_active=True, is_staff=False)
        self.client.force_login(otheruser)

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(401, response.status_code)

    def test_should_allow_admin_user(self) -> None:
        # Given
        self.client.force_login(self.admin_user)

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

    def test_should_not_allow_access_to_non_organisation_admin_user(self) -> None:
        # Given
        self.user.is_staff = False
        self.user.save()

        self.organisation_member.is_admin = False
        self.organisation_member.save()

        self.client.force_login(self.user)

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(401, response.status_code)

    def test_should_use_expected_templates(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "add_organisation_membership.html")

    def test_submitting_blank_form_should_return_expected_errors(self) -> None:
        # When
        response = self.client.post(self.url)

        # Then
        expected_errors = {
            "start_date": ["This field is required."],
            "membership_option": ["This field is required."],
        }

        self.assertDictEqual(expected_errors, response.context["form"].errors)

    def test_start_date_should_default_to_expiry_date_of_latest_membership_if_in_the_future(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        form = response.context["form"]

        expected_start_date = date_format(
            self.organisation_membership.expiry_date(),
            format=settings.SHORT_DATE_FORMAT,
        )

        self.assertEqual(expected_start_date, form.initial["start_date"])

    def test_start_date_should_default_to_today_if_expiry_date_of_latest_membership_has_past(self) -> None:
        # Given
        self.organisation_membership.start_date = (
            timezone.localdate() - self.organisation_membership.membership_option.duration - timedelta(days=1)
        )
        self.organisation_membership.save()

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        form = response.context["form"]

        expected_start_date = date_format(
            timezone.localdate(),
            format=settings.SHORT_DATE_FORMAT,
        )

        self.assertEqual(expected_start_date, form.initial["start_date"])

    def test_should_validate_start_date_does_not_overlap_existing_membership(self) -> None:
        # Given
        start_date = (
            self.organisation_membership.start_date
            + self.organisation_membership.membership_option.duration
            - timedelta(days=1)
        )

        membership_option = MembershipOption.objects.get(name="Second Membership Option")

        form_values = {
            "start_date": date_format(start_date, format=settings.SHORT_DATE_FORMAT),
            "membership_option": membership_option.name,
        }

        # When
        response = self.client.post(
            self.url,
            form_values,
        )

        # Then
        self.assertEqual(200, response.status_code)

        expected_error = ["A new membership can not overlap with an existing membership"]
        self.assertEqual(expected_error, response.context["form"].errors["start_date"])

    def test_should_create_expected_membership(self) -> None:
        # Given
        site = Site.objects.get()

        start_date = self.organisation_membership.start_date + self.organisation_membership.membership_option.duration

        membership_option = MembershipOption.objects.get(name="Second Membership Option")

        form_values = {
            "start_date": date_format(start_date, format=settings.SHORT_DATE_FORMAT),
            "membership_option": membership_option.name,
        }

        # When
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.url, form_values)

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"/users/organisations/view/{self.organisation.pk}/?membership_added=true", response.url)

        organisation_membership = (
            OrganisationMembership.objects.filter(organisation=self.organisation).order_by("-start_date").first()
        )

        with self.subTest("Should create expected organisation membership"):
            self.assertEqual(organisation_membership.membership_option, membership_option)
            self.assertEqual(organisation_membership.start_date, start_date)

        with self.subTest("Should notify staff of new organisation membership"):
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, "New organisation membership")
            self.assertEqual(
                mail.outbox[0].body,
                f"""Hello {self.admin_user.first_name},

{self.organisation.name} has had a new membership added.

Click the link below to review the organisation.

https://{site.domain}/organisations/view/{self.organisation.pk}
""",
            )


@override_settings(BILLING_SERVICE_CLASS="ams.billing.service.MockBillingService")
class AddOrganisationMembershipBillingTests(TestCase):
    def setUp(self) -> None:
        self.user = any_user()

        membership_option = any_membership_option(
            name="First Membership Option", type=MembershipOptionType.ORGANISATION, duration="P1M", cost="1.00"
        )

        start = timezone.localtime() - timedelta(days=7)

        self.organisation = any_organisation()

        self.organisation_member = OrganisationMember.objects.create(
            user=self.user,
            organisation=self.organisation,
            invite_email=self.user.email,
            invite_token="token",
            created_datetime=timezone.localtime(),
            accepted_datetime=timezone.localtime(),
            is_admin=True,
        )

        self.organisation_membership = OrganisationMembership.objects.create(
            organisation=self.organisation,
            membership_option=membership_option,
            created_datetime=start,
            start_date=start.date(),
        )
        Account.objects.create(organisation=self.organisation)

        self.url = f"/users/organisations/add-membership/{self.organisation.pk}/"
        self.client.force_login(self.user)

    @patch("ams.billing.service.MockBillingService.update_organisation_billing_details")
    def test_should_update_organisation_billing_details(self, mock_update_organisation_billing_details: Mock) -> None:
        # Given
        start_date = self.organisation_membership.start_date + self.organisation_membership.membership_option.duration

        form_values = {
            "start_date": date_format(start_date, format=settings.SHORT_DATE_FORMAT),
            "membership_option": self.organisation_membership.membership_option.name,
        }

        # When
        response = self.client.post(self.url, form_values)
        self.assertEqual(302, response.status_code)

        # Then
        mock_update_organisation_billing_details.assert_called_with(self.organisation)

    @patch("ams.billing.service.MockBillingService.update_organisation_billing_details")
    def test_should_show_message_when_error_updating_billing_details(
        self, mock_update_organisation_billing_details: Mock
    ) -> None:
        # Given
        mock_update_organisation_billing_details.side_effect = Exception("any exception")

        start_date = self.organisation_membership.start_date + self.organisation_membership.membership_option.duration

        form_values = {
            "start_date": date_format(start_date, format=settings.SHORT_DATE_FORMAT),
            "membership_option": self.organisation_membership.membership_option.name,
        }

        # When
        response = self.client.post(self.url, form_values)
        self.assertEqual(200, response.status_code)

        # Then
        expected_messages = [
            {
                "value": (
                    "The billing contact could not be created. "
                    "The membership could not be added. "
                    "Please try to add the membership again. "
                    "If this message reappears please contact the site administrator."
                ),
                "type": "error",
            }
        ]
        self.assertEqual(expected_messages, response.context.get("show_messages"))

    @patch("ams.billing.service.MockBillingService.create_invoice")
    def test_should_create_invoice(self, mock_create_invoice: Mock) -> None:
        # Given
        invoice_number = "mock-invoice-number"
        mock_create_invoice.return_value = invoice_number

        start_date = self.organisation_membership.start_date + self.organisation_membership.membership_option.duration

        membership_option = self.organisation_membership.membership_option

        form_values = {
            "start_date": date_format(start_date, format=settings.SHORT_DATE_FORMAT),
            "membership_option": membership_option.name,
        }

        # When
        response = self.client.post(self.url, form_values)
        self.assertEqual(302, response.status_code)

        # Then
        expected_line_items = [
            {
                "description": f"{membership_option.name} ${membership_option.cost} for 1 month",
                "unit_amount": Decimal(membership_option.cost),
                "quantity": 1,
            }
        ]

        issue_date = mock_create_invoice.call_args.args[1]
        due_date = mock_create_invoice.call_args.args[2]

        with self.subTest("should use expected issue date and due date"):
            self.assertEqual(timezone.localtime().date(), issue_date.date())
            self.assertEqual(issue_date + relativedelta(months=1), due_date)

        with self.subTest("should call create_invoice with expected values"):
            mock_create_invoice.assert_called_with(self.organisation.account, issue_date, due_date, expected_line_items)

    @patch("ams.billing.service.MockBillingService.create_invoice")
    def test_should_show_message_when_error_creating_invoice(self, mock_create_invoice: Mock) -> None:
        # Given
        mock_create_invoice.side_effect = Exception("any exception")

        start_date = self.organisation_membership.start_date + self.organisation_membership.membership_option.duration

        form_values = {
            "start_date": date_format(start_date, format=settings.SHORT_DATE_FORMAT),
            "membership_option": self.organisation_membership.membership_option.name,
        }

        # When
        response = self.client.post(self.url, form_values)
        self.assertEqual(200, response.status_code)

        # Then
        expected_messages = [
            {
                "value": (
                    "The invoice could not be created. "
                    "The membership could not be added. "
                    "Please try to add the membership again. "
                    "If this message reappears please contact the site administrator."
                ),
                "type": "error",
            }
        ]
        self.assertEqual(expected_messages, response.context.get("show_messages"))
