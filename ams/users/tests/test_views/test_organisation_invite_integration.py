# ruff: noqa: S106

"""Integration tests for organisation invites sent before user signup."""

from http import HTTPStatus

import pytest
from django.test import Client
from django.urls import reverse

from ams.organisations.tests.factories import OrganisationFactory
from ams.organisations.tests.factories import OrganisationMemberFactory
from ams.users.models import User

pytestmark = pytest.mark.django_db


class TestOrganisationInviteBeforeSignupIntegration:
    """Integration tests for the full flow of inviting a non-existent user."""

    def test_complete_flow_invite_before_signup(self, client: Client):
        """Test the complete flow: invite sent, user signs up, sees invite, accepts.

        This test verifies the bug fix where invites sent to emails of users
        who don't yet exist are visible after the user signs up.
        """
        # Step 1: Organisation admin creates an org and sends an invite to
        # non-existent user
        admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="testpass123",
            first_name="Admin",
            last_name="User",
        )
        organisation = OrganisationFactory(name="Test Organisation")

        # Admin is automatically added as admin when org is created
        OrganisationMemberFactory(
            user=admin,
            organisation=organisation,
            accepted_datetime__not_none=True,
            role="ADMIN",
        )

        # Send invite to email that doesn't have a user account yet
        invite_email = "newuser@example.com"
        invite = OrganisationMemberFactory(
            invite=True,  # user=None
            invite_email=invite_email,
            organisation=organisation,
        )

        # Verify invite was created with no user
        assert invite.user is None
        assert invite.invite_email == invite_email
        assert invite.accepted_datetime is None

        # Step 2: New user signs up with the invited email
        new_user = User.objects.create_user(
            username="newuser",
            email=invite_email,
            password="testpass123",
            first_name="New",
            last_name="User",
        )

        # Step 3: New user logs in and views their dashboard
        client.force_login(new_user)
        user_detail_url = reverse(
            "users:detail",
            kwargs={"username": new_user.username},
        )
        response = client.get(user_detail_url)

        assert response.status_code == HTTPStatus.OK

        # Step 4: Verify the invite is visible in pending invitations
        assert response.context["has_pending_invitations"] is True
        pending_invitations = list(response.context["pending_invitation_table"].data)
        assert len(pending_invitations) == 1
        assert pending_invitations[0].uuid == invite.uuid
        assert pending_invitations[0].organisation.name == "Test Organisation"

        # Step 5: User accepts the invite
        accept_url = reverse(
            "organisations:accept_invite",
            kwargs={"invite_token": invite.invite_token},
        )
        accept_response = client.post(accept_url, follow=True)

        assert accept_response.status_code == HTTPStatus.OK

        # Step 6: Verify invite was accepted and user is now linked
        invite.refresh_from_db()
        assert invite.user == new_user
        assert invite.accepted_datetime is not None

        # Step 7: Verify dashboard now shows accepted organisation
        response = client.get(user_detail_url)
        assert response.status_code == HTTPStatus.OK
        assert response.context["has_organisations"] is True
        assert response.context["has_pending_invitations"] is False

        accepted_orgs = list(response.context["organisation_table"].data)
        assert len(accepted_orgs) == 1
        assert accepted_orgs[0].organisation.name == "Test Organisation"

    def test_invite_before_signup_case_insensitive(self, client: Client):
        """Test that invite matching works case-insensitively."""
        organisation = OrganisationFactory()

        # Send invite with uppercase email
        invite_email = "NEWUSER@EXAMPLE.COM"
        invite = OrganisationMemberFactory(
            invite=True,
            invite_email=invite_email,
            organisation=organisation,
        )

        # User signs up with lowercase email
        new_user = User.objects.create_user(
            username="newuser",
            email="newuser@example.com",  # lowercase
            password="testpass123",
            first_name="New",
            last_name="User",
        )

        # Login and check dashboard
        client.force_login(new_user)
        user_detail_url = reverse(
            "users:detail",
            kwargs={"username": new_user.username},
        )
        response = client.get(user_detail_url)

        assert response.status_code == HTTPStatus.OK
        assert response.context["has_pending_invitations"] is True
        pending_invitations = list(response.context["pending_invitation_table"].data)
        assert len(pending_invitations) == 1
        assert pending_invitations[0].uuid == invite.uuid

    def test_multiple_invites_before_signup(self, client: Client):
        """Test user sees all invites sent before signup."""
        org1 = OrganisationFactory(name="Organisation 1")
        org2 = OrganisationFactory(name="Organisation 2")
        org3 = OrganisationFactory(name="Organisation 3")

        invite_email = "newuser@example.com"

        # Create multiple invites to the same email
        invite1 = OrganisationMemberFactory(
            invite=True,
            invite_email=invite_email,
            organisation=org1,
        )
        invite2 = OrganisationMemberFactory(
            invite=True,
            invite_email=invite_email,
            organisation=org2,
        )
        invite3 = OrganisationMemberFactory(
            invite=True,
            invite_email=invite_email,
            organisation=org3,
        )

        # User signs up
        new_user = User.objects.create_user(
            username="newuser",
            email=invite_email,
            password="testpass123",
            first_name="New",
            last_name="User",
        )

        # Login and check dashboard
        client.force_login(new_user)
        user_detail_url = reverse(
            "users:detail",
            kwargs={"username": new_user.username},
        )
        response = client.get(user_detail_url)

        assert response.status_code == HTTPStatus.OK
        assert response.context["has_pending_invitations"] is True
        pending_invitations = list(response.context["pending_invitation_table"].data)
        expected_invitations = 3
        assert len(pending_invitations) == expected_invitations

        invite_uuids = {inv.uuid for inv in pending_invitations}
        assert invite1.uuid in invite_uuids
        assert invite2.uuid in invite_uuids
        assert invite3.uuid in invite_uuids

    def test_declined_invite_redirects_to_dashboard(self, client: Client):
        """Test that declining an invite redirects back to dashboard."""
        organisation = OrganisationFactory(name="Test Organisation")
        invite_email = "newuser@example.com"

        invite = OrganisationMemberFactory(
            invite=True,
            invite_email=invite_email,
            organisation=organisation,
        )

        # User signs up
        new_user = User.objects.create_user(
            username="newuser",
            email=invite_email,
            password="testpass123",
            first_name="New",
            last_name="User",
        )

        # Login and decline the invite
        client.force_login(new_user)
        decline_url = reverse(
            "organisations:decline_invite",
            kwargs={"invite_token": invite.invite_token},
        )
        decline_response = client.post(decline_url, follow=True)

        assert decline_response.status_code == HTTPStatus.OK

        # Verify invite was declined and user is linked
        invite.refresh_from_db()
        assert invite.user == new_user
        assert invite.declined_datetime is not None

        # Verify dashboard no longer shows the invite
        user_detail_url = reverse(
            "users:detail",
            kwargs={"username": new_user.username},
        )
        response = client.get(user_detail_url)
        assert response.context["has_pending_invitations"] is False
