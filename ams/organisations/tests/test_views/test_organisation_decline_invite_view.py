"""Tests for DeclineOrganisationInviteView."""

from http import HTTPStatus

import pytest
from django.urls import reverse
from django.utils import timezone

from ams.organisations.tests.factories import OrganisationFactory
from ams.organisations.tests.factories import OrganisationMemberFactory
from ams.users.models import User
from ams.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestDeclineOrganisationInviteView:
    """Tests for the decline organisation invite view."""

    def test_decline_invite_as_existing_user(self, client):
        """Test declining an invitation as an existing user."""
        user = UserFactory()
        org = OrganisationFactory()

        # Create pending invitation for the user
        member = OrganisationMemberFactory(
            organisation=org,
            user=user,
            accepted_datetime=None,
            declined_datetime=None,
        )

        client.force_login(user)
        url = reverse(
            "organisations:decline_invite",
            kwargs={"invite_token": member.invite_token},
        )

        response = client.get(url)

        # Should redirect to user detail page
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "users:detail",
            kwargs={"username": user.username},
        )

        # Refresh member from database
        member.refresh_from_db()

        # Should have declined_datetime set
        assert member.declined_datetime is not None
        # Should not have accepted_datetime set
        assert member.accepted_datetime is None

    def test_decline_invite_wrong_user(self, client):
        """Test that a user cannot decline another user's invitation."""
        user1 = UserFactory()
        user2 = UserFactory()
        org = OrganisationFactory()

        # Create invitation for user1
        member = OrganisationMemberFactory(
            organisation=org,
            user=user1,
            accepted_datetime=None,
            declined_datetime=None,
        )

        # Try to decline as user2
        client.force_login(user2)
        url = reverse(
            "organisations:decline_invite",
            kwargs={"invite_token": member.invite_token},
        )

        response = client.get(url)

        # Should redirect to user redirect
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("users:redirect")

        # Refresh member from database
        member.refresh_from_db()

        # Should not have declined_datetime set
        assert member.declined_datetime is None

    def test_decline_already_accepted_invite(self, client):
        """Test declining an invitation that was already accepted."""
        user = UserFactory()
        org = OrganisationFactory()

        # Create accepted invitation
        member = OrganisationMemberFactory(
            organisation=org,
            user=user,
            accepted_datetime=timezone.now(),
            declined_datetime=None,
        )

        client.force_login(user)
        url = reverse(
            "organisations:decline_invite",
            kwargs={"invite_token": member.invite_token},
        )

        response = client.get(url)

        # Should redirect to organisation detail
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "organisations:detail",
            kwargs={"uuid": org.uuid},
        )

        # Refresh member from database
        member.refresh_from_db()

        # Should still not have declined_datetime set
        assert member.declined_datetime is None

    def test_decline_already_declined_invite(self, client):
        """Test declining an invitation that was already declined."""
        user = UserFactory()
        org = OrganisationFactory()

        # Create declined invitation
        declined_time = timezone.now()
        member = OrganisationMemberFactory(
            organisation=org,
            user=user,
            accepted_datetime=None,
            declined_datetime=declined_time,
        )

        client.force_login(user)
        url = reverse(
            "organisations:decline_invite",
            kwargs={"invite_token": member.invite_token},
        )

        response = client.get(url)

        # Should redirect to user redirect
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("users:redirect")

        # Refresh member from database
        member.refresh_from_db()

        # declined_datetime should not change
        assert member.declined_datetime == declined_time

    def test_decline_invite_not_authenticated(self, client):
        """Test that unauthenticated users are redirected to login."""
        org = OrganisationFactory()
        member = OrganisationMemberFactory(
            organisation=org,
            user=None,
            invite_email="test@example.com",
            accepted_datetime=None,
            declined_datetime=None,
        )

        url = reverse(
            "organisations:decline_invite",
            kwargs={"invite_token": member.invite_token},
        )

        response = client.get(url)

        # Should redirect to login
        assert response.status_code == HTTPStatus.FOUND
        assert "/accounts/login/" in response.url

    def test_decline_invite_new_user_matching_email(self, client):
        """Test declining an invitation as a new user with matching email."""
        org = OrganisationFactory()
        invite_email = "newuser@example.com"

        # Create invitation sent to email (no user yet)
        member = OrganisationMemberFactory(
            organisation=org,
            user=None,
            invite_email=invite_email,
            accepted_datetime=None,
            declined_datetime=None,
        )

        # Create and login as new user with matching email
        user = UserFactory(email=invite_email)
        client.force_login(user)

        url = reverse(
            "organisations:decline_invite",
            kwargs={"invite_token": member.invite_token},
        )

        response = client.get(url)

        # Should redirect to user detail
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "users:detail",
            kwargs={"username": user.username},
        )

        # Refresh member from database
        member.refresh_from_db()

        # Should have declined_datetime set
        assert member.declined_datetime is not None
        # Should link to the user
        assert member.user == user

    def test_decline_invite_new_user_wrong_email(self, client):
        """Test declining fails when new user email doesn't match invite."""
        org = OrganisationFactory()

        # Create invitation sent to specific email
        member = OrganisationMemberFactory(
            organisation=org,
            user=None,
            invite_email="invited@example.com",
            accepted_datetime=None,
            declined_datetime=None,
        )

        # Login as user with different email
        user = UserFactory(email="different@example.com")
        client.force_login(user)

        url = reverse(
            "organisations:decline_invite",
            kwargs={"invite_token": member.invite_token},
        )

        response = client.get(url)

        # Should redirect to user redirect
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("users:redirect")

        # Refresh member from database
        member.refresh_from_db()

        # Should not have declined_datetime set
        assert member.declined_datetime is None
        # Should not link to the user
        assert member.user is None

    def test_decline_revoked_invite(self, user: User, client):
        """Test that revoked invites cannot be declined."""
        org = OrganisationFactory()
        member = OrganisationMemberFactory(
            organisation=org,
            user=user,
            accepted_datetime=None,
            revoked_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse(
            "organisations:decline_invite",
            kwargs={"invite_token": member.invite_token},
        )
        response = client.get(url, follow=True)

        assert response.status_code == HTTPStatus.OK
        messages = list(response.context["messages"])
        assert any("revoked" in str(m).lower() for m in messages)
        member.refresh_from_db()
        assert member.declined_datetime is None
