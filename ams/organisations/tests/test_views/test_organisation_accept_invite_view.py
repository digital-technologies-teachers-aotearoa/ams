from datetime import timedelta
from http import HTTPStatus

import pytest
from allauth.account.models import EmailAddress
from django.urls import reverse
from django.utils import timezone

from ams.memberships.tests.factories import MembershipOptionFactory
from ams.memberships.tests.factories import OrganisationMembershipFactory
from ams.organisations.tests.factories import OrganisationFactory
from ams.organisations.tests.factories import OrganisationMemberFactory
from ams.users.models import User
from ams.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
class TestAcceptOrganisationInviteView:
    """Tests for the AcceptOrganisationInviteView"""

    def test_accept_invite_as_existing_user(self, user: User, client):
        """Test accepting an invite as an existing user."""
        org = OrganisationFactory()
        member = OrganisationMemberFactory(
            organisation=org,
            user=user,
            invite_email=user.email,
            accepted_datetime=None,
        )

        client.force_login(user)
        url = reverse(
            "organisations:accept_invite",
            kwargs={"invite_token": member.invite_token},
        )

        response = client.get(url)

        # Should redirect
        assert response.status_code == HTTPStatus.FOUND

        # Member should be accepted
        member.refresh_from_db()
        assert member.accepted_datetime is not None

    def test_accept_invite_when_seats_full(self, user: User, client):
        """Test that accepting an invite fails when seats are full."""
        org = OrganisationFactory()

        # Create membership with 2 seats
        membership_option = MembershipOptionFactory(
            type="ORGANISATION",
            max_seats=2,
        )
        OrganisationMembershipFactory(
            organisation=org,
            membership_option=membership_option,
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timedelta(days=365),
            approved=True,
        )

        # Fill both seats
        OrganisationMemberFactory(
            organisation=org,
            user=UserFactory(),
            accepted_datetime=timezone.now(),
        )
        OrganisationMemberFactory(
            organisation=org,
            user=UserFactory(),
            accepted_datetime=timezone.now(),
        )

        # Try to accept invite
        member = OrganisationMemberFactory(
            organisation=org,
            user=user,
            invite_email=user.email,
            accepted_datetime=None,
        )

        client.force_login(user)
        url = reverse(
            "organisations:accept_invite",
            kwargs={"invite_token": member.invite_token},
        )

        response = client.get(url)

        # Should redirect
        assert response.status_code == HTTPStatus.FOUND

        # Member should NOT be accepted
        member.refresh_from_db()
        assert member.accepted_datetime is None

    def test_accept_already_accepted_invite(self, user: User, client):
        """Test that accepting an already-accepted invite redirects gracefully."""
        org = OrganisationFactory()
        member = OrganisationMemberFactory(
            organisation=org,
            user=user,
            accepted_datetime=timezone.now(),  # Already accepted
        )

        client.force_login(user)
        url = reverse(
            "organisations:accept_invite",
            kwargs={"invite_token": member.invite_token},
        )

        response = client.get(url)

        # Should redirect
        assert response.status_code == HTTPStatus.FOUND

    def test_accept_already_declined_invite(self, user: User, client):
        """Test that accepting a declined invite is not allowed."""
        org = OrganisationFactory()
        member = OrganisationMemberFactory(
            organisation=org,
            user=user,
            accepted_datetime=None,
            declined_datetime=timezone.now(),  # Already declined
        )

        client.force_login(user)
        url = reverse(
            "organisations:accept_invite",
            kwargs={"invite_token": member.invite_token},
        )

        response = client.get(url)

        # Should redirect to user redirect page
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("users:redirect")

        # Member should still be declined, not accepted
        member.refresh_from_db()
        assert member.accepted_datetime is None
        assert member.declined_datetime is not None

    def test_accept_invite_not_authenticated(self, client):
        """Test that unauthenticated users are redirected to login."""
        org = OrganisationFactory()
        member = OrganisationMemberFactory(
            organisation=org,
            accepted_datetime=None,
        )

        url = reverse(
            "organisations:accept_invite",
            kwargs={"invite_token": member.invite_token},
        )

        response = client.get(url)

        # Should redirect to login
        assert response.status_code == HTTPStatus.FOUND
        assert "/accounts/login/" in response.url

    def test_accept_invite_wrong_user(self, client):
        """Test that a different user cannot accept another user's invite."""
        wrong_user = UserFactory()
        correct_user = UserFactory()

        org = OrganisationFactory()
        member = OrganisationMemberFactory(
            organisation=org,
            user=correct_user,  # Invite is for correct_user
            invite_email=correct_user.email,
            accepted_datetime=None,
        )

        client.force_login(wrong_user)  # But wrong_user tries to accept
        url = reverse(
            "organisations:accept_invite",
            kwargs={"invite_token": member.invite_token},
        )

        response = client.get(url)

        # Should redirect to home (not allowed)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("users:redirect")

        # Member should NOT be accepted
        member.refresh_from_db()
        assert member.accepted_datetime is None

    def test_accept_invite_new_user_matching_email(self, client):
        """Test new user can accept invite if their email matches invite_email."""
        org = OrganisationFactory()
        invite_email = "newuser@example.com"

        # Create invite for non-user
        member = OrganisationMemberFactory(
            organisation=org,
            user=None,  # No user yet
            invite_email=invite_email,
            accepted_datetime=None,
        )

        # Create new user with matching email
        new_user = UserFactory(email=invite_email)
        client.force_login(new_user)

        url = reverse(
            "organisations:accept_invite",
            kwargs={"invite_token": member.invite_token},
        )

        response = client.get(url)

        # Should redirect
        assert response.status_code == HTTPStatus.FOUND

        # Member should be accepted and linked to user
        member.refresh_from_db()
        assert member.accepted_datetime is not None
        assert member.user == new_user

    def test_accept_invite_new_user_matching_email_case_insensitive(self, client):
        """Test email matching is case-insensitive."""
        org = OrganisationFactory()
        invite_email = "NewUser@Example.COM"

        # Create invite for non-user with mixed case email
        member = OrganisationMemberFactory(
            organisation=org,
            user=None,
            invite_email=invite_email,
            accepted_datetime=None,
        )

        # Create new user with lowercase email
        new_user = UserFactory(email="newuser@example.com")
        client.force_login(new_user)

        url = reverse(
            "organisations:accept_invite",
            kwargs={"invite_token": member.invite_token},
        )

        response = client.get(url)

        # Should redirect (success)
        assert response.status_code == HTTPStatus.FOUND

        # Member should be accepted and linked to user
        member.refresh_from_db()
        assert member.accepted_datetime is not None
        assert member.user == new_user

    def test_accept_invite_new_user_wrong_email(self, client):
        """Test new user cannot accept invite if their email doesn't match."""
        org = OrganisationFactory()
        invite_email = "invited@example.com"

        # Create invite for non-user
        member = OrganisationMemberFactory(
            organisation=org,
            user=None,
            invite_email=invite_email,
            accepted_datetime=None,
        )

        # Create new user with different email
        wrong_user = UserFactory(email="different@example.com")
        client.force_login(wrong_user)

        url = reverse(
            "organisations:accept_invite",
            kwargs={"invite_token": member.invite_token},
        )

        response = client.get(url)

        # Should redirect to home (not allowed)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("users:redirect")

        # Member should NOT be accepted
        member.refresh_from_db()
        assert member.accepted_datetime is None
        assert member.user is None

    def test_accept_invite_new_user_no_invite_email(self, client):
        """Test that invites without invite_email set can still be accepted."""
        org = OrganisationFactory()

        # Create invite without invite_email (edge case)
        member = OrganisationMemberFactory(
            organisation=org,
            user=None,
            invite_email="",  # Empty string
            accepted_datetime=None,
        )

        new_user = UserFactory()
        client.force_login(new_user)

        url = reverse(
            "organisations:accept_invite",
            kwargs={"invite_token": member.invite_token},
        )

        response = client.get(url)

        # Should allow acceptance (no email validation when invite_email is empty)
        assert response.status_code == HTTPStatus.FOUND

        # Member should be accepted
        member.refresh_from_db()
        assert member.accepted_datetime is not None
        assert member.user == new_user

    def test_accept_invite_redirects_to_user_page(self, user: User, client):
        """Test that accepting an invite redirects to the user detail page."""
        org = OrganisationFactory()
        member = OrganisationMemberFactory(
            organisation=org,
            user=user,
            invite_email=user.email,
            accepted_datetime=None,
        )

        client.force_login(user)
        url = reverse(
            "organisations:accept_invite",
            kwargs={"invite_token": member.invite_token},
        )

        response = client.get(url)

        # Should redirect to user detail page
        expected_url = reverse("users:detail", kwargs={"username": user.username})
        assert response.url == expected_url

    def test_accept_already_accepted_invite_redirects_to_user_page(
        self,
        user: User,
        client,
    ):
        """Test that re-accepting an invite redirects to the user detail page."""
        org = OrganisationFactory()
        member = OrganisationMemberFactory(
            organisation=org,
            user=user,
            accepted_datetime=timezone.now(),  # Already accepted
        )

        client.force_login(user)
        url = reverse(
            "organisations:accept_invite",
            kwargs={"invite_token": member.invite_token},
        )

        response = client.get(url)

        # Should redirect to user detail page
        expected_url = reverse("users:detail", kwargs={"username": user.username})
        assert response.url == expected_url

    def test_accept_invite_when_seats_full_redirects_to_user_page(
        self,
        user: User,
        client,
    ):
        """Test that seats full error redirects to the user detail page."""
        org = OrganisationFactory()

        # Create membership with 2 seats
        membership_option = MembershipOptionFactory(
            type="ORGANISATION",
            max_seats=2,
        )
        OrganisationMembershipFactory(
            organisation=org,
            membership_option=membership_option,
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timedelta(days=365),
        )

        # Fill both seats
        OrganisationMemberFactory(
            organisation=org,
            user=UserFactory(),
            accepted_datetime=timezone.now(),
        )
        OrganisationMemberFactory(
            organisation=org,
            user=UserFactory(),
            accepted_datetime=timezone.now(),
        )

        # Try to accept invite
        member = OrganisationMemberFactory(
            organisation=org,
            user=user,
            invite_email=user.email,
            accepted_datetime=None,
        )

        client.force_login(user)
        url = reverse(
            "organisations:accept_invite",
            kwargs={"invite_token": member.invite_token},
        )

        response = client.get(url)

        # Should redirect to user detail page
        expected_url = reverse("users:detail", kwargs={"username": user.username})
        assert response.url == expected_url

    def test_accept_revoked_invite(self, user: User, client):
        """Test that revoked invites cannot be accepted."""
        org = OrganisationFactory()
        member = OrganisationMemberFactory(
            organisation=org,
            user=user,
            accepted_datetime=None,
            revoked_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse(
            "organisations:accept_invite",
            kwargs={"invite_token": member.invite_token},
        )
        response = client.get(url, follow=True)

        assert response.status_code == HTTPStatus.OK
        messages = list(response.context["messages"])
        assert any("revoked" in str(m).lower() for m in messages)
        member.refresh_from_db()
        assert member.accepted_datetime is None

    def test_accept_invite_sent_to_secondary_verified_email(self, client):
        """Test user can accept invite sent to their secondary verified email."""
        org = OrganisationFactory()
        secondary_email = "secondary@example.com"

        # Create invite for non-user with secondary email
        member = OrganisationMemberFactory(
            organisation=org,
            user=None,  # No user yet
            invite_email=secondary_email,
            accepted_datetime=None,
        )

        # Create user with different primary email
        user = UserFactory(email="primary@example.com")

        # Add secondary verified email to the user
        EmailAddress.objects.create(
            user=user,
            email=secondary_email,
            verified=True,
            primary=False,
        )

        client.force_login(user)
        url = reverse(
            "organisations:accept_invite",
            kwargs={"invite_token": member.invite_token},
        )

        response = client.get(url)

        # Should redirect (success)
        assert response.status_code == HTTPStatus.FOUND

        # Member should be accepted and linked to user
        member.refresh_from_db()
        assert member.accepted_datetime is not None
        assert member.user == user

    def test_accept_invite_sent_to_unverified_secondary_email_fails(self, client):
        """Test user cannot accept invite sent to their unverified secondary email."""
        org = OrganisationFactory()
        unverified_email = "unverified@example.com"

        # Create invite for non-user
        member = OrganisationMemberFactory(
            organisation=org,
            user=None,
            invite_email=unverified_email,
            accepted_datetime=None,
        )

        # Create user with different primary email
        user = UserFactory(email="primary@example.com")

        # Add UNVERIFIED secondary email to the user
        EmailAddress.objects.create(
            user=user,
            email=unverified_email,
            verified=False,  # Not verified
            primary=False,
        )

        client.force_login(user)
        url = reverse(
            "organisations:accept_invite",
            kwargs={"invite_token": member.invite_token},
        )

        response = client.get(url)

        # Should redirect to home (not allowed)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("users:redirect")

        # Member should NOT be accepted
        member.refresh_from_db()
        assert member.accepted_datetime is None
        assert member.user is None
