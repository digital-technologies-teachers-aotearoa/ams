from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from ...test.utils import parse_response_table_rows
from ..models import MembershipOption, MembershipOptionType


class AdminMembershipOptionListTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="testadminuser", is_staff=True)

        self.membership_option = MembershipOption.objects.create(
            name="Membership Option", type=MembershipOptionType.INDIVIDUAL, duration="P1M", cost="1.00"
        )

        self.url = "/users/membership-options/"
        self.client.force_login(self.user)

    def test_should_not_allow_access_to_non_admin_user(self) -> None:
        # Given
        self.user.is_staff = False
        self.user.save()

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
        self.assertTemplateUsed(response, "admin_membership_options.html")
        self.assertTemplateUsed(response, "admin_membership_option_actions.html")

    def test_should_show_expected_columns(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_columns = ["name", "type", "duration", "cost", "actions"]
        columns = [column.name for column in response.context["table"].columns]
        self.assertListEqual(expected_columns, columns)

    def test_should_show_expected_headings(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_columns = ["Name", "Type", "Duration", "Cost", "Actions"]
        columns = [column.header for column in response.context["table"].columns]
        self.assertListEqual(expected_columns, columns)

    def test_should_show_expected_rows(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        rows = parse_response_table_rows(response)

        expected_rows = [
            [
                self.membership_option.name,
                self.membership_option.type.label,
                "1 month",
                Decimal(self.membership_option.cost),
                "Edit",
            ]
        ]

        self.assertListEqual(expected_rows, rows)
