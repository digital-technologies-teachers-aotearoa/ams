from datetime import timedelta

from dateutil.tz import gettz
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from django.utils.formats import date_format

from ...test.utils import (
    any_invoice,
    any_organisation,
    any_user_account,
    parse_response_table_rows,
)
from ..models import (
    MembershipOption,
    MembershipOptionType,
    OrganisationMember,
    UserMembership,
)


class UserViewTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="testuser", is_staff=False)
        self.user.first_name = "John"
        self.user.last_name = "Smith"
        self.user.email = "user@example.com"
        self.user.save()

        self.time_zone = gettz(settings.TIME_ZONE)

        membership_option = MembershipOption.objects.create(
            name="Membership Option", type=MembershipOptionType.INDIVIDUAL, duration="P1M", cost="1.00"
        )

        start = timezone.localtime() - membership_option.duration + timedelta(days=7)

        self.user_membership = UserMembership.objects.create(
            user=self.user,
            membership_option=membership_option,
            start_date=start.date(),
            created_datetime=start,
            approved_datetime=start,
        )

        self.organisation = any_organisation()

        self.organisation_member = OrganisationMember.objects.create(
            user=self.user, organisation=self.organisation, created_datetime=start, accepted_datetime=start
        )

        self.account = any_user_account(user=self.user)
        self.invoice = any_invoice(account=self.account, invoice_number="INV-0001")

        self.url = "/users/current/"
        self.client.force_login(self.user)

    def test_should_require_logged_in_user(self) -> None:
        # Given
        self.client.logout()

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual("/users/login/?next=/users/current/", response.url)

    def test_should_redirect_admin_to_admin_user_view(self) -> None:
        # Given
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"/users/view/{self.user.pk}/", response.url)

    def test_should_use_expected_templates(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "user_view.html")
        self.assertTemplateUsed(response, "user_membership_actions.html")

    def test_should_show_add_membership_button_if_latest_membership_is_active(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)
        self.assertEqual(True, response.context["can_add_membership"])

    def test_should_show_add_membership_button_if_latest_membership_is_expired(self) -> None:
        # Given
        self.user_membership.start_date = (
            timezone.localtime() - self.user_membership.membership_option.duration
        ).date()
        self.user_membership.save()

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)
        self.assertEqual(True, response.context["can_add_membership"])

    def test_should_not_show_add_membership_button_if_latest_membership_is_pending(self) -> None:
        # Given
        UserMembership.objects.create(
            user=self.user,
            membership_option=self.user_membership.membership_option,
            start_date=self.user_membership.expiry_date(),
            created_datetime=timezone.localtime(),
            approved_datetime=None,
        )

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)
        self.assertEqual(False, response.context["can_add_membership"])

    def test_should_show_expected_membership_columns(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_columns = ["membership", "duration", "status", "start_date", "approved_date", "actions"]
        columns = [column.name for column in response.context["tables"][0].columns]
        self.assertListEqual(expected_columns, columns)

    def test_should_show_expected_membership_headings(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_headings = ["Membership", "Duration", "Status", "Start Date", "Approved Date", "Actions"]
        headings = [column.header for column in response.context["tables"][0].columns]
        self.assertListEqual(expected_headings, headings)

    def test_should_not_show_approve_membership_action(self) -> None:
        # Given
        self.user_membership.approved_datetime = None
        self.user_membership.save()

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        rows = parse_response_table_rows(response, 0)

        expected_rows = [
            [
                self.user_membership.membership_option.name,
                "1 month",
                "Pending",
                date_format(self.user_membership.start_date, format="SHORT_DATE_FORMAT"),
                "—",
                "",
            ]
        ]

        self.assertListEqual(expected_rows, rows)

    def test_should_show_expected_organisation_members_columns(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_columns = ["organisation", "status", "join_date", "role", "actions"]
        columns = [column.name for column in response.context["tables"][2].columns]
        self.assertListEqual(expected_columns, columns)

    def test_should_show_expected_organisation_members_headings(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_headings = ["Organisation", "Status", "Join Date", "Role", "Actions"]
        headings = [column.header for column in response.context["tables"][2].columns]
        self.assertListEqual(expected_headings, headings)

    def test_should_show_expected_user_organisation_members(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        rows = parse_response_table_rows(response, 2)

        self.maxDiff = None

        expected_rows = [
            [
                self.organisation_member.organisation.name,
                "Active",
                date_format(self.organisation_member.accepted_datetime, format="SHORT_DATE_FORMAT"),
                "Member",
                "",
            ]
        ]

        self.assertListEqual(expected_rows, rows)

    def test_should_show_expected_user_organisation_member_actions_if_admin(self) -> None:
        # Given
        self.organisation_member.is_admin = True
        self.organisation_member.save()

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        rows = parse_response_table_rows(response, 2)

        self.maxDiff = None

        expected_rows = [
            [
                self.organisation_member.organisation.name,
                "Active",
                date_format(self.organisation_member.accepted_datetime, format="SHORT_DATE_FORMAT"),
                "Admin",
                "View",
            ]
        ]

        self.assertListEqual(expected_rows, rows)

    def test_should_show_expected_invoice_columns(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_columns = ["invoice_number", "issue_date", "due_date", "amount", "paid", "due", "actions"]
        columns = [column.name for column in response.context["tables"][1].columns]
        self.assertListEqual(expected_columns, columns)

    def test_should_show_expected_invoice_headings(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_headings = ["Invoice Number", "Issue Date", "Due Date", "Amount", "Paid", "Due", "Actions"]
        headings = [column.header for column in response.context["tables"][1].columns]
        self.assertListEqual(expected_headings, headings)

    def test_should_show_expected_invoices(self) -> None:
        # Given
        any_invoice()

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        rows = parse_response_table_rows(response, 1)

        self.maxDiff = None

        expected_rows = [
            [
                self.invoice.invoice_number,
                date_format(self.invoice.issue_date, format="SHORT_DATE_FORMAT"),
                date_format(self.invoice.due_date, format="SHORT_DATE_FORMAT"),
                self.invoice.amount,
                self.invoice.paid,
                self.invoice.due,
                "",
            ]
        ]

        self.assertListEqual(expected_rows, rows)
