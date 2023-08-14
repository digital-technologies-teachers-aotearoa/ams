from datetime import datetime

from dateutil.tz import gettz
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.formats import date_format

from ..models import MembershipOption, MembershipOptionType, UserMembership


class AdminUserListTests(TestCase):
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

        self.user_membership = UserMembership.objects.create(
            user=self.user,
            membership_option=membership_option,
            created_datetime=datetime(day=1, month=7, year=2023, hour=6, tzinfo=self.time_zone),
            approved_datetime=datetime(day=1, month=7, year=2023, hour=21, tzinfo=self.time_zone),
        )

        self.url = f"/users/view/{self.user.pk}/"
        self.client.force_login(self.admin_user)

    def test_should_not_allow_access_to_non_admin_user(self) -> None:
        # Given
        self.client.force_login(self.user)

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(403, response.status_code)

    def test_should_use_expected_templates(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "admin_user_view.html")
        self.assertTemplateUsed(response, "admin_user_view_membership_actions.html")

    def test_should_show_expected_membership_columns(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_membership_columns = ["membership", "duration", "status", "start_date", "approved_date", "actions"]
        columns = [column.name for column in response.context["table"].columns]
        self.assertListEqual(expected_membership_columns, columns)

    def test_should_show_expected_membership_headings(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_membership_headings = ["Membership", "Duration", "Status", "Start Date", "Approved Date", "Actions"]
        headings = [column.header for column in response.context["table"].columns]
        self.assertListEqual(expected_membership_headings, headings)

    def test_should_show_expected_rows(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        rows = []
        for row in response.context["table"].rows:
            row_cells = [cell for cell in row.cells]

            # Ignore the actions column
            row_cells.pop()

            rows.append(row_cells)

        expected_rows = [
            [
                self.user_membership.membership_option.name,
                "1 month",
                "Approved",
                date_format(self.user_membership.created_datetime, format="SHORT_DATE_FORMAT"),
                date_format(self.user_membership.approved_datetime, format="SHORT_DATE_FORMAT"),
            ]
        ]

        self.assertListEqual(expected_rows, rows)
