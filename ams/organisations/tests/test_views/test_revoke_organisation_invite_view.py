from http import HTTPStatus

import pytest
from django.urls import reverse
from django.utils import timezone

from ams.organisations.models import OrganisationMember
from ams.organisations.tests.factories import OrganisationFactory
from ams.organisations.tests.factories import OrganisationMemberFactory
from ams.users.models import User

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
class TestRevokeOrganisationInviteView:
    """Tests for RevokeOrganisationInviteView."""

    def test_org_admin_can_revoke_pending_invite(self, user: User, client):
        """Test that an org admin can revoke a pending invite (deletes record)."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        # Create a pending invite
        pending_invite = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=None,
            declined_datetime=None,
        )
        pending_invite_id = pending_invite.id

        client.force_login(user)
        url = reverse(
            "organisations:revoke_invite",
            kwargs={"uuid": org.uuid, "member_uuid": pending_invite.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        # Member record should be deleted (not just marked as revoked)
        assert not OrganisationMember.objects.filter(id=pending_invite_id).exists()

    def test_staff_can_revoke_invite(self, user: User, client):
        """Test that staff can revoke an invite (deletes record)."""
        user.is_staff = True
        user.save()

        org = OrganisationFactory()
        pending_invite = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=None,
            declined_datetime=None,
        )
        pending_invite_id = pending_invite.id

        client.force_login(user)
        url = reverse(
            "organisations:revoke_invite",
            kwargs={"uuid": org.uuid, "member_uuid": pending_invite.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        # Member record should be deleted (not just marked as revoked)
        assert not OrganisationMember.objects.filter(id=pending_invite_id).exists()

    def test_cannot_revoke_accepted_invite(self, user: User, client):
        """Test that accepted invites cannot be revoked."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        # Create an accepted member
        accepted_member = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse(
            "organisations:revoke_invite",
            kwargs={"uuid": org.uuid, "member_uuid": accepted_member.uuid},
        )
        response = client.post(url, follow=True)

        assert response.status_code == HTTPStatus.OK
        messages = list(response.context["messages"])
        assert any("already been accepted" in str(m).lower() for m in messages)
        accepted_member.refresh_from_db()
        assert accepted_member.revoked_datetime is None

    def test_cannot_revoke_declined_invite(self, user: User, client):
        """Test that declined invites cannot be revoked."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        # Create a declined invite
        declined_invite = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=None,
            declined_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse(
            "organisations:revoke_invite",
            kwargs={"uuid": org.uuid, "member_uuid": declined_invite.uuid},
        )
        response = client.post(url, follow=True)

        assert response.status_code == HTTPStatus.OK
        messages = list(response.context["messages"])
        assert any("already been declined" in str(m).lower() for m in messages)
        declined_invite.refresh_from_db()
        assert declined_invite.revoked_datetime is None

    def test_cannot_revoke_already_revoked_invite(self, user: User, client):
        """Test that already revoked invites show info message."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        # Create a revoked invite
        revoked_invite = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=None,
            declined_datetime=None,
            revoked_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse(
            "organisations:revoke_invite",
            kwargs={"uuid": org.uuid, "member_uuid": revoked_invite.uuid},
        )
        response = client.post(url, follow=True)

        assert response.status_code == HTTPStatus.OK
        messages = list(response.context["messages"])
        assert any("already been revoked" in str(m).lower() for m in messages)

    def test_non_admin_cannot_revoke_invite(self, user: User, client):
        """Test that non-admin members cannot revoke invites."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        )
        pending_invite = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=None,
        )

        client.force_login(user)
        url = reverse(
            "organisations:revoke_invite",
            kwargs={"uuid": org.uuid, "member_uuid": pending_invite.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FORBIDDEN
        pending_invite.refresh_from_db()
        assert pending_invite.revoked_datetime is None

    def test_non_member_cannot_revoke_invite(self, user: User, client):
        """Test that non-members cannot revoke invites."""
        org = OrganisationFactory()
        pending_invite = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=None,
        )

        client.force_login(user)
        url = reverse(
            "organisations:revoke_invite",
            kwargs={"uuid": org.uuid, "member_uuid": pending_invite.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FORBIDDEN
        pending_invite.refresh_from_db()
        assert pending_invite.revoked_datetime is None

    def test_unauthenticated_cannot_revoke_invite(self, client):
        """Test that unauthenticated users cannot revoke invites."""
        org = OrganisationFactory()
        pending_invite = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=None,
        )

        url = reverse(
            "organisations:revoke_invite",
            kwargs={"uuid": org.uuid, "member_uuid": pending_invite.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        pending_invite.refresh_from_db()
        assert pending_invite.revoked_datetime is None

    def test_revoke_shows_success_message(self, user: User, client):
        """Test that revoking shows a success message with email."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        pending_invite = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=None,
            invite_email="test@example.com",
        )

        client.force_login(user)
        url = reverse(
            "organisations:revoke_invite",
            kwargs={"uuid": org.uuid, "member_uuid": pending_invite.uuid},
        )
        response = client.post(url, follow=True)

        assert response.status_code == HTTPStatus.OK
        messages = list(response.context["messages"])
        assert any("revoked invite" in str(m).lower() for m in messages)
        assert any("test@example.com" in str(m) for m in messages)
