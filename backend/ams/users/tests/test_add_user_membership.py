from datetime import timedelta

from dateutil.tz import gettz
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.utils import timezone
from django.utils.formats import date_format

from ..models import MembershipOption, MembershipOptionType, UserMembership


class AddUserMembershipTests(TestCase):
    def setUp(self) -> None:
        self.admin_user = User.objects.create_user(
            username="testadminuser", first_name="Admin", email="user@example.com", is_staff=True
        )

        self.user = User.objects.create_user(username="testuser", is_staff=False)
        self.user.first_name = "John"
        self.user.last_name = "Smith"
        self.user.email = "user@example.com"
        self.user.save()

        self.time_zone = gettz(settings.TIME_ZONE)

        membership_option = MembershipOption.objects.create(
            name="First Membership Option", type=MembershipOptionType.INDIVIDUAL, duration="P1M", cost="1.00"
        )
        MembershipOption.objects.create(
            name="Second Membership Option", type=MembershipOptionType.INDIVIDUAL, duration="P2M", cost="2.00"
        )

        start = timezone.localtime() - timedelta(days=7)

        self.user_membership = UserMembership.objects.create(
            user=self.user,
            membership_option=membership_option,
            created_datetime=start,
            start_date=start.date(),
            approved_datetime=start + timedelta(days=1),
        )

        self.url = f"/users/add-membership/{self.user.pk}/"
        self.client.force_login(self.user)

    def test_should_require_logged_in_user(self) -> None:
        # Given
        self.client.logout()

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(401, response.status_code)

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

    def test_should_use_expected_templates(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "add_user_membership.html")

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
            self.user_membership.expiry_date(),
            format=settings.SHORT_DATE_FORMAT,
        )

        self.assertEqual(expected_start_date, form.initial["start_date"])

    def test_start_date_should_default_to_today_if_expiry_date_of_latest_membership_has_past(self) -> None:
        # Given
        self.user_membership.start_date = (
            timezone.localdate() - self.user_membership.membership_option.duration - timedelta(days=1)
        )
        self.user_membership.save()

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
            self.user_membership.start_date + self.user_membership.membership_option.duration - timedelta(days=1)
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
        start_date = self.user_membership.start_date + self.user_membership.membership_option.duration

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
        self.assertEqual("/users/current/?membership_added=true", response.url)

        user_membership = UserMembership.objects.filter(user=self.user).order_by("-start_date").first()

        with self.subTest("Should create expected user membership"):
            self.assertEqual(user_membership.membership_option, membership_option)
            self.assertEqual(user_membership.start_date, start_date)
            self.assertEqual(user_membership.approved_datetime, None)

        with self.subTest("Should notify staff of new user membership"):
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, "New user membership")
            self.assertEqual(
                mail.outbox[0].body,
                f"""Hello {self.admin_user.first_name},

A user has added a new membership and needs approval.

Click the link below to review the user and approve their membership.

https://testserver/users/view/{user_membership.user.id}
""",
            )
