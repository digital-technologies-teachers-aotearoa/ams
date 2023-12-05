from datetime import timedelta
from urllib.parse import quote

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from pydiscourse.sso import sso_payload

from ...users.models import (
    MembershipOption,
    MembershipOptionType,
    Organisation,
    OrganisationMember,
    OrganisationMembership,
    OrganisationType,
    UserMembership,
)


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

        start = timezone.localtime() - timedelta(days=7)
        self.user_membership = UserMembership.objects.create(
            user=self.user,
            membership_option=membership_option,
            start_date=start.date(),
            created_datetime=start,
            approved_datetime=start,
        )

        self.organisation = Organisation.objects.create(
            type=OrganisationType.objects.create(name="Primary School"),
            name="Any Organisation",
            telephone="555-12345",
            contact_name="John Smith",
            email="john@example.com",
            street_address="123 Main Street",
            suburb="",
            city="Capital City",
            postal_code="8080",
            postal_address="PO BOX 1234\nCapital City 8082",
        )

        organisation_membership_option = MembershipOption.objects.create(
            name="Organisation Membership Option", type=MembershipOptionType.ORGANISATION, duration="P1M", cost="1.00"
        )

        self.organisation_membership = OrganisationMembership.objects.create(
            organisation=self.organisation,
            membership_option=organisation_membership_option,
            created_datetime=start,
            start_date=start.date(),
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

    def test_should_allow_user_with_active_user_membership(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        expected_url_prefix = settings.DISCOURSE_REDIRECT_DOMAIN + "/session/sso_login"
        self.assertEqual(302, response.status_code)
        self.assertTrue(response.url.startswith(expected_url_prefix), response.url)

    def test_should_allow_user_with_active_membership_through_organisation(self) -> None:
        # Given
        self.user_membership.delete()

        OrganisationMember.objects.create(
            user=self.user,
            organisation=self.organisation,
            created_datetime=self.organisation_membership.created_datetime,
            accepted_datetime=self.organisation_membership.created_datetime,
        )

        # When
        response = self.client.get(self.url)

        # Then
        expected_url_prefix = settings.DISCOURSE_REDIRECT_DOMAIN + "/session/sso_login"
        self.assertEqual(302, response.status_code)
        self.assertTrue(response.url.startswith(expected_url_prefix), response.url)

    def test_should_not_allow_user_with_non_accepted_organisation_member(self) -> None:
        # Given
        self.user_membership.delete()

        OrganisationMember.objects.create(
            user=self.user,
            organisation=self.organisation,
            created_datetime=self.organisation_membership.created_datetime,
            accepted_datetime=None,
        )

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual("/users/current/?requires_membership=true", response.url)

    def test_should_not_allow_user_with_cancelled_organisation_membership(self) -> None:
        # Given
        self.user_membership.delete()

        OrganisationMember.objects.create(
            user=self.user,
            organisation=self.organisation,
            created_datetime=self.organisation_membership.created_datetime,
            accepted_datetime=self.organisation_membership.created_datetime,
        )

        self.organisation_membership.cancelled_datetime = self.organisation_membership.created_datetime
        self.organisation_membership.save()

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual("/users/current/?requires_membership=true", response.url)

    def test_should_not_allow_user_with_expired_organisation_membership(self) -> None:
        # Given
        self.user_membership.delete()

        OrganisationMember.objects.create(
            user=self.user,
            organisation=self.organisation,
            created_datetime=self.organisation_membership.created_datetime,
            accepted_datetime=self.organisation_membership.created_datetime,
        )

        self.organisation_membership.start_date = (timezone.localtime() - relativedelta(months=2)).date()
        self.organisation_membership.save()

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual("/users/current/?requires_membership=true", response.url)

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
