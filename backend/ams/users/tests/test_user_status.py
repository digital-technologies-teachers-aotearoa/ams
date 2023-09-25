from datetime import timedelta

from django.contrib.sites.requests import RequestSite
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from registration.models import RegistrationProfile

from ..models import MembershipOption, MembershipOptionType, UserMembership


class UserStatusTests(TestCase):
    def setUp(self) -> None:
        request = RequestFactory().get("/")

        self.user = RegistrationProfile.objects.create_inactive_user(
            RequestSite(request),
            username="user@example.com",
            email="user@example.com",
            first_name="John",
            last_name="Smith",
            password="valid password",
        )

        self.user.is_active = True
        self.user.save()

        membership_option = MembershipOption.objects.create(
            name="Membership Option", type=MembershipOptionType.INDIVIDUAL, duration="P1M", cost="1.00"
        )

        start = timezone.localtime()
        self.user_membership = UserMembership.objects.create(
            user=self.user,
            membership_option=membership_option,
            start_date=start.date(),
            created_datetime=start,
            approved_datetime=None,
        )

    def test_get_login_screen(self) -> None:
        # When
        response = self.client.get("/users/login/")

        # Then
        self.assertTemplateUsed(response, "registration/login.html")

    def test_should_login_successfully_with_valid_details(self) -> None:
        # When
        response = self.client.post(
            "/users/login/",
            {
                "username": self.user.username,
                "password": "valid password",
            },
        )

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(response.url, "/")

    def test_should_redirect_to_next_url_on_successful_login(self) -> None:
        # When
        response = self.client.post(
            "/users/login/",
            {"username": self.user.username, "password": "valid password", "next": "/membership/"},
        )

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(response.url, "/membership/")

    def test_should_show_error_with_invalid_details(self) -> None:
        # When
        response = self.client.post(
            "/users/login/",
            {
                "username": self.user.username,
                "password": "invalid password",
            },
        )

        # Then
        self.assertContains(response, "Invalid email or password")

    def test_should_show_logged_in_users_first_and_last_name(self) -> None:
        # Given
        self.client.force_login(self.user)

        # When
        response = self.client.get("/")

        # Then
        self.assertRegex(str(response.content), f"You are logged in as.+ {self.user.first_name} {self.user.last_name}")

    def test_should_show_logged_in_nameless_users_username(self) -> None:
        # Given
        self.user.first_name = ""
        self.user.last_name = ""
        self.user.save()

        self.client.force_login(self.user)

        # When
        response = self.client.get("/")

        # Then
        self.assertRegex(str(response.content), f"You are logged in as.+ {self.user.username}")

    def test_should_not_show_logged_out_users_name(self) -> None:
        # When
        response = self.client.get("/")

        # Then
        self.assertNotContains(response, "You are logged in as")

    def test_should_show_logged_in_users_pending_membership_status(self) -> None:
        # Given
        self.client.force_login(self.user)

        # When
        response = self.client.get("/")

        # Then
        self.assertContains(response, "Your membership is Pending")

    def test_should_show_logged_in_users_pending_membership_future_start_date(self) -> None:
        # Given
        self.user_membership.start_date = timezone.localdate() + timedelta(days=1)
        self.user_membership.approved_datetime = timezone.now()
        self.user_membership.save()

        self.client.force_login(self.user)

        # When
        response = self.client.get("/")

        # Then
        start_date_string = date_format(self.user_membership.start_date, "DATE_FORMAT")
        self.assertContains(response, f"Your membership is Pending (starts on {start_date_string})")

    def test_should_show_logged_in_users_pending_membership_future_start_date_after_current_membership_expired(
        self,
    ) -> None:
        # Given
        self.user_membership.start_date = timezone.localdate() - self.user_membership.membership_option.duration
        self.user_membership.save()

        new_membership = UserMembership.objects.create(
            user=self.user_membership.user,
            membership_option=self.user_membership.membership_option,
            start_date=timezone.localdate() + timedelta(days=1),
            approved_datetime=timezone.now(),
            created_datetime=timezone.now(),
        )

        self.client.force_login(self.user)

        # When
        response = self.client.get("/")

        # Then
        start_date_string = date_format(new_membership.start_date, "DATE_FORMAT")
        self.assertContains(response, f"Your membership is Pending (starts on {start_date_string})")

    def test_should_show_logged_in_users_active_membership_status(self) -> None:
        # Given
        self.user_membership.approved_datetime = timezone.now()
        self.user_membership.save()

        self.client.force_login(self.user)

        # When
        response = self.client.get("/")

        # Then
        self.assertContains(response, "Your membership is Active")

    def test_should_show_logged_in_users_expired_membership_status(self) -> None:
        # Given
        self.user_membership.approved_datetime = timezone.now()
        self.user_membership.start_date = timezone.localdate() - self.user_membership.membership_option.duration
        self.user_membership.save()

        self.client.force_login(self.user)

        # When
        response = self.client.get("/")

        # Then
        self.assertContains(response, "Your membership has Expired")
        self.assertContains(
            response, '<a href="%s">Extend</a>' % reverse("add-user-membership", kwargs={"pk": self.user.pk})
        )

    def test_should_show_active_membership_expires_in_days_lte_30_days(self) -> None:
        # Given
        self.user_membership.membership_option.duration = "P30D"
        self.user_membership.membership_option.save()

        self.user_membership.approved_datetime = timezone.now()
        self.user_membership.start_date = timezone.localdate()
        self.user_membership.save()

        self.client.force_login(self.user)

        # When
        response = self.client.get("/")

        # Then
        self.assertContains(response, "Your membership is Active")
        self.assertContains(response, "expires in 30 days")
        self.assertContains(
            response, '<a href="%s">Extend</a>' % reverse("add-user-membership", kwargs={"pk": self.user.pk})
        )

    def test_should_not_show_active_membership_expires_in_days_gt_30_days(self) -> None:
        # Given
        self.user_membership.membership_option.duration = "P31D"
        self.user_membership.membership_option.save()

        self.user_membership.approved_datetime = timezone.now()
        self.user_membership.start_date = timezone.localdate()
        self.user_membership.save()

        self.client.force_login(self.user)

        # When
        response = self.client.get("/")

        # Then
        self.assertContains(response, "Your membership is Active")
        self.assertNotContains(response, "expires in")

    def test_should_include_admin_menu_for_admin_user(self) -> None:
        # Given
        self.user.is_staff = True
        self.user.save()

        self.client.force_login(self.user)

        # When
        response = self.client.get("/")
        self.assertContains(response, "user-details-admin-btn")

    def test_should_not_include_admin_menu_for_non_admin_user(self) -> None:
        # Given
        self.user.is_staff = False
        self.user.save()

        self.client.force_login(self.user)

        # When
        response = self.client.get("/")
        self.assertNotContains(response, "user-details-admin-btn")
