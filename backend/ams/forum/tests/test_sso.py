from urllib.parse import quote

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from pydiscourse.sso import sso_payload

from ...users.models import MembershipOption, MembershipOptionType, UserMembership


class ForumRedirectTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="testuser", is_staff=False)
        self.user.save()

        self.url = "/forum/"
        self.client.force_login(self.user)

    def test_should_require_logged_in_user(self) -> None:
        # Given
        self.client.logout()

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual("/users/login/?next=/forum/", response.url)

        response = self.client.get(response.url)

        self.assertContains(response, "You must be logged in to view this feature.")

    def test_should_redirect_to_forum_sso_url(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(settings.DISCOURSE_REDIRECT_DOMAIN + "/session/sso?return_path=/", response.url)


class ForumSingleSignOnTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="testuser", is_staff=False)
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
            approved_datetime=start,
        )

        payload_query_string = sso_payload(settings.DISCOURSE_CONNECT_SECRET, nonce="nonce")
        self.url = "/forum/sso?" + payload_query_string
        self.client.force_login(self.user)

    def test_should_require_logged_in_user(self) -> None:
        # Given
        self.client.logout()

        # When
        response = self.client.get(self.url)

        # Then
        quoted_url = quote(self.url)
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"/users/login/?next={quoted_url}", response.url)

    def test_sso_callback_should_show_message_if_no_active_membership(self) -> None:
        # Given
        self.user_membership.delete()

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual("/users/current/?requires_membership=true", response.url)

        response = self.client.get(response.url)

        expected_messages = [{"value": "You must have an active membership to view this feature.", "type": "error"}]
        self.assertEqual(expected_messages, response.context.get("show_messages"))

    def test_should_allow_user_with_active_membership(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        expected_url_prefix = settings.DISCOURSE_REDIRECT_DOMAIN + "/session/sso_login"
        self.assertEqual(302, response.status_code)
        self.assertTrue(response.url.startswith(expected_url_prefix), response.url)

    def test_should_allow_admin_user_without_active_membership(self) -> None:
        # Given
        self.user.is_staff = True
        self.user.save()
        self.user_membership.delete()

        # When
        response = self.client.get(self.url)

        # Then
        expected_url_prefix = settings.DISCOURSE_REDIRECT_DOMAIN + "/session/sso_login"
        self.assertEqual(302, response.status_code)
        self.assertTrue(response.url.startswith(expected_url_prefix))
