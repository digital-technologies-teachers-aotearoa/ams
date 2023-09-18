from django.contrib.sites.requests import RequestSite
from django.test import RequestFactory, TestCase
from django.utils import timezone
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

    def test_should_not_show_logged_in_users_approved_membership_status(self) -> None:
        # Given
        self.user_membership.approved_datetime = timezone.now()
        self.user_membership.save()

        self.client.force_login(self.user)

        # When
        response = self.client.get("/")

        # Then
        self.assertNotContains(response, "Your membership is")

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
