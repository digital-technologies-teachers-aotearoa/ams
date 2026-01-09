"""Integration tests for the full organisation invite flow."""

from http import HTTPStatus

import pytest
from django.urls import reverse
from django.utils import timezone

from ams.organisations.models import OrganisationMember
from ams.organisations.tests.factories import OrganisationFactory
from ams.organisations.tests.factories import OrganisationMemberFactory
from ams.users.models import User
from ams.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestOrganisationInviteFlow:
    """Integration tests for invite, decline, reinvite, and accept flows."""

    def test_invite_decline_reinvite_accept_flow(self, user: User, client, mailoutbox):
        """Test the full flow: invite -> decline -> reinvite -> accept."""
        # Setup: Create org with admin
        org = OrganisationFactory()
        admin = user
        OrganisationMemberFactory(
            organisation=org,
            user=admin,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        # Create the user who will be invited
        invitee = UserFactory(email="invitee@example.com")

        # Step 1: Admin invites the user
        client.force_login(admin)
        invite_url = reverse("organisations:invite_member", kwargs={"uuid": org.uuid})
        response = client.post(invite_url, data={"email": invitee.email})

        assert response.status_code == HTTPStatus.FOUND
        assert len(mailoutbox) == 1

        # Verify invite was created
        member = OrganisationMember.objects.get(
            organisation=org,
            invite_email=invitee.email,
        )
        assert member.user == invitee
        assert member.accepted_datetime is None
        invite_token = member.invite_token

        # Step 2: Invitee declines the invitation
        client.force_login(invitee)
        decline_url = reverse(
            "organisations:decline_invite",
            kwargs={"invite_token": invite_token},
        )
        response = client.get(decline_url)

        assert response.status_code == HTTPStatus.FOUND

        # Verify the invite record was deleted
        assert not OrganisationMember.objects.filter(
            organisation=org,
            invite_email=invitee.email,
        ).exists()

        # Step 3: Admin re-invites the same user
        client.force_login(admin)
        response = client.post(invite_url, data={"email": invitee.email})

        assert response.status_code == HTTPStatus.FOUND
        expected_emails = 2
        assert len(mailoutbox) == expected_emails  # Second email sent

        # Verify new invite was created
        new_member = OrganisationMember.objects.get(
            organisation=org,
            invite_email=invitee.email,
        )
        assert new_member.user == invitee
        assert new_member.accepted_datetime is None
        new_invite_token = new_member.invite_token

        # Step 4: Invitee accepts the new invitation
        client.force_login(invitee)
        accept_url = reverse(
            "organisations:accept_invite",
            kwargs={"invite_token": new_invite_token},
        )
        response = client.get(accept_url)

        assert response.status_code == HTTPStatus.FOUND

        # Verify the user is now an active member
        new_member.refresh_from_db()
        assert new_member.accepted_datetime is not None
        assert new_member.declined_datetime is None

    def test_invite_revoke_reinvite_accept_flow(self, user: User, client, mailoutbox):
        """Test the full flow: invite -> revoke -> reinvite -> accept."""
        # Setup: Create org with admin
        org = OrganisationFactory()
        admin = user
        OrganisationMemberFactory(
            organisation=org,
            user=admin,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        # Create the user who will be invited
        invitee = UserFactory(email="invitee@example.com")

        # Step 1: Admin invites the user
        client.force_login(admin)
        invite_url = reverse("organisations:invite_member", kwargs={"uuid": org.uuid})
        response = client.post(invite_url, data={"email": invitee.email})

        assert response.status_code == HTTPStatus.FOUND
        assert len(mailoutbox) == 1

        # Verify invite was created
        member = OrganisationMember.objects.get(
            organisation=org,
            invite_email=invitee.email,
        )
        member_uuid = member.uuid

        # Step 2: Admin revokes the invitation
        revoke_url = reverse(
            "organisations:revoke_invite",
            kwargs={"uuid": org.uuid, "member_uuid": member_uuid},
        )
        response = client.post(revoke_url)

        assert response.status_code == HTTPStatus.FOUND

        # Verify the invite record was deleted
        assert not OrganisationMember.objects.filter(
            organisation=org,
            invite_email=invitee.email,
        ).exists()

        # Step 3: Admin re-invites the same user
        response = client.post(invite_url, data={"email": invitee.email})

        assert response.status_code == HTTPStatus.FOUND
        expected_emails = 2
        assert len(mailoutbox) == expected_emails  # Second email sent

        # Verify new invite was created
        new_member = OrganisationMember.objects.get(
            organisation=org,
            invite_email=invitee.email,
        )
        new_invite_token = new_member.invite_token

        # Step 4: Invitee accepts the new invitation
        client.force_login(invitee)
        accept_url = reverse(
            "organisations:accept_invite",
            kwargs={"invite_token": new_invite_token},
        )
        response = client.get(accept_url)

        assert response.status_code == HTTPStatus.FOUND

        # Verify the user is now an active member
        new_member.refresh_from_db()
        assert new_member.accepted_datetime is not None
        assert new_member.declined_datetime is None
