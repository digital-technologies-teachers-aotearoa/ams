from datetime import timedelta

from dateutil.tz import gettz
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from django.utils.formats import date_format

from ...test.utils import parse_response_table_rows
from ..models import MembershipOption, MembershipOptionType, UserMembership


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

    def test_should_not_show_approve_membership_action(self) -> None:
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
                self.user_membership.membership_option.name,
                "1 month",
                "Pending",
                date_format(self.user_membership.start_date, format="SHORT_DATE_FORMAT"),
                "—",
                "",
            ]
        ]

        self.assertListEqual(expected_rows, rows)
