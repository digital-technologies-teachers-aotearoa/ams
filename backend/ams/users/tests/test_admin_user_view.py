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


class AdminUserViewTests(TestCase):
    def setUp(self) -> None:
        self.admin_user = User.objects.create_user(username="testadminuser", is_staff=True)

        self.user = User.objects.create_user(username="testuser", is_staff=False)
        self.user.first_name = "John"
        self.user.last_name = "Smith"
        self.user.email = "user@example.com"
        self.user.save()

        self.time_zone = gettz(settings.TIME_ZONE)

        membership_option = MembershipOption.objects.create(
            name="Membership Option", type=MembershipOptionType.INDIVIDUAL, duration="P1M", cost="1.00"
        )

        start = timezone.localtime() - timedelta(days=7)

        self.user_membership = UserMembership.objects.create(
            user=self.user,
            membership_option=membership_option,
            created_datetime=start,
            start_date=start.date(),
            approved_datetime=start + timedelta(days=1),
        )

        self.organisation = any_organisation()

        self.organisation_member = OrganisationMember.objects.create(
            user=self.user, organisation=self.organisation, created_datetime=start, accepted_datetime=start
        )

        self.account = any_user_account(user=self.user)
        self.invoice = any_invoice(account=self.account, invoice_number="INV-0001")

        self.url = f"/users/view/{self.user.pk}/"
        self.client.force_login(self.admin_user)

    def test_should_not_allow_get_access_to_non_admin_user(self) -> None:
        # Given
        self.client.force_login(self.user)

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(403, response.status_code)

    def test_should_not_allow_post_access_to_non_admin_user(self) -> None:
        # Given
        self.client.force_login(self.user)

        # When
        response = self.client.post(self.url)

        # Then
        self.assertEqual(403, response.status_code)

    def test_should_use_expected_templates(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "user_view.html")
        self.assertTemplateUsed(response, "admin_user_membership_actions.html")

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

    def test_should_show_expected_rows(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        rows = parse_response_table_rows(response, 0)

        expected_rows = [
            [
                self.user_membership.membership_option.name,
                "1 month",
                "Active",
                date_format(self.user_membership.start_date, format="SHORT_DATE_FORMAT"),
                date_format(self.user_membership.approved_datetime, format="SHORT_DATE_FORMAT"),
                "Cancel",
            ]
        ]

        self.assertListEqual(expected_rows, rows)

    def test_should_show_unapproved_user_membership_as_pending(self) -> None:
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
                "Approve,Cancel",
            ]
        ]

        self.assertListEqual(expected_rows, rows)

    def test_should_approve_unapproved_user_membership(self) -> None:
        # When
        self.user_membership.approved_datetime = None
        self.user_membership.save()

        response = self.client.post(
            self.url, data={"action": "approve_user_membership", "user_membership_id": self.user_membership.id}
        )

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"{self.url}?membership_approved=true", response.url)

        response = self.client.get(response.url)

        self.assertEqual(200, response.status_code)

        rows = parse_response_table_rows(response)

        expected_rows = [
            [
                self.user_membership.membership_option.name,
                "1 month",
                "Active",
                date_format(self.user_membership.start_date, format="SHORT_DATE_FORMAT"),
                date_format(timezone.now().astimezone(self.time_zone), format="SHORT_DATE_FORMAT"),
                "Cancel",
            ]
        ]

        self.assertListEqual(expected_rows, rows)

        expected_messages = [{"value": "Membership Approved", "type": "success"}]
        self.assertListEqual(expected_messages, response.context["show_messages"])

    def test_should_not_re_approve_user_membership(self) -> None:
        # When
        response = self.client.post(
            self.url, data={"action": "approve_user_membership", "user_membership_id": self.user_membership.id}
        )

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(self.url, response.url)

    def test_should_not_approve_user_membership_with_invalid_id(self) -> None:
        # When
        response = self.client.post(self.url, data={"action": "approve_user_membership", "user_membership_id": -1})

        # Then
        self.assertEqual(400, response.status_code)

    def test_should_show_expired_membership_as_expired(self) -> None:
        # Given
        self.user_membership.approved_datetime = timezone.now().astimezone(self.time_zone)
        self.user_membership.start_date = timezone.localdate() - self.user_membership.membership_option.duration
        self.user_membership.save()

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        rows = parse_response_table_rows(response, 0)

        self.maxDiff = None

        expected_rows = [
            [
                self.user_membership.membership_option.name,
                "1 month",
                "Expired",
                date_format(self.user_membership.start_date, format="SHORT_DATE_FORMAT"),
                date_format(self.user_membership.approved_datetime, format="SHORT_DATE_FORMAT"),
                "",
            ]
        ]

        self.assertListEqual(expected_rows, rows)

    def test_should_cancel_uncancelled_user_membership(self) -> None:
        # When
        response = self.client.post(
            self.url, data={"action": "cancel_user_membership", "user_membership_id": self.user_membership.id}
        )

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"{self.url}?membership_cancelled=true", response.url)

        response = self.client.get(response.url)

        self.assertEqual(200, response.status_code)

        rows = parse_response_table_rows(response, 0)

        expected_rows = [
            [
                self.user_membership.membership_option.name,
                "1 month",
                "Cancelled",
                date_format(self.user_membership.start_date, format="SHORT_DATE_FORMAT"),
                date_format(self.user_membership.approved_datetime, format="SHORT_DATE_FORMAT"),
                "",
            ]
        ]

        self.assertListEqual(expected_rows, rows)

        expected_messages = [{"value": "Membership Cancelled", "type": "success"}]
        self.assertListEqual(expected_messages, response.context["show_messages"])

    def test_should_not_cancel_cancelled_user_membership(self) -> None:
        # Given
        self.user_membership.cancelled_datetime = timezone.now()
        self.user_membership.save()

        # When
        response = self.client.post(
            self.url, data={"action": "cancel_user_membership", "user_membership_id": self.user_membership.id}
        )

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(self.url, response.url)

    def test_should_not_cancel_expired_user_membership(self) -> None:
        # Given
        self.user_membership.start_date = timezone.localdate() - self.user_membership.membership_option.duration
        self.user_membership.save()

        # When
        response = self.client.post(
            self.url, data={"action": "cancel_user_membership", "user_membership_id": self.user_membership.id}
        )

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(self.url, response.url)

    def test_should_show_cancelled_membership_as_cancelled(self) -> None:
        # Given
        self.user_membership.cancelled_datetime = timezone.now().astimezone(self.time_zone)
        self.user_membership.save()

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        rows = parse_response_table_rows(response, 0)

        self.maxDiff = None

        expected_rows = [
            [
                self.user_membership.membership_option.name,
                "1 month",
                "Cancelled",
                date_format(self.user_membership.start_date, format="SHORT_DATE_FORMAT"),
                date_format(self.user_membership.approved_datetime, format="SHORT_DATE_FORMAT"),
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
