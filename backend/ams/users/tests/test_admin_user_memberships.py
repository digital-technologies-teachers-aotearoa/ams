from datetime import datetime

from dateutil.tz import gettz
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from django.utils.formats import date_format

from ...test.utils import parse_response_table_rows
from ..models import MembershipOption, MembershipOptionType, UserMembership


class AdminUserMembershipsTests(TestCase):
    def setUp(self) -> None:
        self.admin_user = User.objects.create_user(username="testadminuser", is_staff=True)

        self.user = User.objects.create_user(username="testuser", is_staff=False)
        self.user.first_name = "John"
        self.user.last_name = "Smith"
        self.user.email = "user@example.com"
        self.user.save()

        membership_option = MembershipOption.objects.create(
            name="Membership Option", type=MembershipOptionType.INDIVIDUAL, duration="P1M", cost="1.00"
        )

        self.time_zone = gettz(settings.TIME_ZONE)

        self.user_membership = UserMembership.objects.create(
            user=self.user,
            membership_option=membership_option,
            created_datetime=datetime(day=1, month=7, year=2023, hour=6, tzinfo=self.time_zone),
            approved_datetime=datetime(day=1, month=7, year=2023, hour=21, tzinfo=self.time_zone),
        )

        self.url = "/users/memberships/"
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
        self.assertTemplateUsed(response, "admin_user_memberships.html")
        self.assertTemplateUsed(response, "admin_user_membership_actions.html")

    def test_should_show_expected_columns(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_columns = ["full_name", "membership", "duration", "status", "start_date", "approved_date", "actions"]
        columns = [column.name for column in response.context["table"].columns]
        self.assertListEqual(expected_columns, columns)

    def test_should_show_expected_headings(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_headings = ["Full Name", "Membership", "Duration", "Status", "Start Date", "Approved Date", "Actions"]
        headings = [column.header for column in response.context["table"].columns]
        self.assertListEqual(expected_headings, headings)

    def test_should_show_expected_rows(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        rows = parse_response_table_rows(response)

        expected_rows = [
            [
                self.user.get_full_name(),
                self.user_membership.membership_option.name,
                "1 month",
                "Active",
                date_format(self.user_membership.created_datetime, format="SHORT_DATE_FORMAT"),
                date_format(self.user_membership.approved_datetime, format="SHORT_DATE_FORMAT"),
                "",
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

        rows = parse_response_table_rows(response)

        expected_rows = [
            [
                self.user.get_full_name(),
                self.user_membership.membership_option.name,
                "1 month",
                "Pending",
                date_format(self.user_membership.created_datetime, format="SHORT_DATE_FORMAT"),
                "—",
                "Approve",
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
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "admin_user_memberships.html")
        self.assertTemplateUsed(response, "admin_user_membership_actions.html")

        rows = parse_response_table_rows(response)

        expected_rows = [
            [
                self.user.get_full_name(),
                self.user_membership.membership_option.name,
                "1 month",
                "Active",
                date_format(self.user_membership.created_datetime, format="SHORT_DATE_FORMAT"),
                date_format(timezone.now().astimezone(self.time_zone), format="SHORT_DATE_FORMAT"),
                "",
            ]
        ]
        self.assertListEqual(expected_rows, rows)

        expected_messages = ["Membership Approved"]
        self.assertListEqual(expected_messages, response.context["show_messages"])

    def test_should_not_re_approve_user_membership(self) -> None:
        # When
        response = self.client.post(
            self.url, data={"action": "approve_user_membership", "user_membership_id": self.user_membership.id}
        )

        # Then
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "admin_user_memberships.html")
        self.assertTemplateUsed(response, "admin_user_membership_actions.html")

        self.assertEqual(None, response.context.get("show_messages"))

    def test_should_not_approve_user_membership_with_invalid_id(self) -> None:
        # When
        response = self.client.post(self.url, data={"action": "approve_user_membership", "user_membership_id": -1})

        # Then
        self.assertEqual(400, response.status_code)
