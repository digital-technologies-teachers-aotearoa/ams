from http import HTTPStatus

import pytest
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from ams.organisations.models import OrganisationMember
from ams.organisations.tests.factories import OrganisationFactory
from ams.organisations.tests.factories import OrganisationMemberFactory
from ams.users.models import User

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
class TestResendOrganisationInviteView:
    """Tests for ResendOrganisationInviteView."""

    def test_org_admin_can_resend_pending_invite(self, user: User, client):
        """Test that an org admin can resend a pending invite."""
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
            invite_email="test@example.com",
        )
        original_token = pending_invite.invite_token

        client.force_login(user)
        url = reverse(
            "organisations:resend_invite",
            kwargs={"uuid": org.uuid, "member_uuid": pending_invite.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        # Member record should still exist (not deleted like revoke)
        pending_invite.refresh_from_db()
        assert pending_invite.invite_token == original_token
        # last_sent_datetime should be updated
        assert pending_invite.last_sent_datetime is not None

    def test_staff_can_resend_invite(self, user: User, client):
        """Test that staff can resend an invite."""
        user.is_staff = True
        user.save()

        org = OrganisationFactory()
        pending_invite = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=None,
            declined_datetime=None,
            invite_email="test@example.com",
        )
        original_token = pending_invite.invite_token

        client.force_login(user)
        url = reverse(
            "organisations:resend_invite",
            kwargs={"uuid": org.uuid, "member_uuid": pending_invite.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        # Member record should still exist
        pending_invite.refresh_from_db()
        assert pending_invite.invite_token == original_token

    def test_cannot_resend_accepted_invite(self, user: User, client):
        """Test that accepted invites cannot be resent."""
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
            "organisations:resend_invite",
            kwargs={"uuid": org.uuid, "member_uuid": accepted_member.uuid},
        )
        response = client.post(url, follow=True)

        assert response.status_code == HTTPStatus.OK
        messages = list(response.context["messages"])
        assert any("already been accepted" in str(m).lower() for m in messages)

    def test_cannot_resend_declined_invite(self, user: User, client):
        """Test that declined invites cannot be resent."""
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
            "organisations:resend_invite",
            kwargs={"uuid": org.uuid, "member_uuid": declined_invite.uuid},
        )
        response = client.post(url, follow=True)

        assert response.status_code == HTTPStatus.OK
        messages = list(response.context["messages"])
        assert any("already been declined" in str(m).lower() for m in messages)

    def test_cannot_resend_revoked_invite(self, user: User, client):
        """Test that revoked invites cannot be resent."""
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
            "organisations:resend_invite",
            kwargs={"uuid": org.uuid, "member_uuid": revoked_invite.uuid},
        )
        response = client.post(url, follow=True)

        assert response.status_code == HTTPStatus.OK
        messages = list(response.context["messages"])
        assert any("already been revoked" in str(m).lower() for m in messages)

    def test_non_admin_cannot_resend_invite(self, user: User, client):
        """Test that non-admin members cannot resend invites."""
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
            "organisations:resend_invite",
            kwargs={"uuid": org.uuid, "member_uuid": pending_invite.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_non_member_cannot_resend_invite(self, user: User, client):
        """Test that non-members cannot resend invites."""
        org = OrganisationFactory()
        pending_invite = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=None,
        )

        client.force_login(user)
        url = reverse(
            "organisations:resend_invite",
            kwargs={"uuid": org.uuid, "member_uuid": pending_invite.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_unauthenticated_cannot_resend_invite(self, client):
        """Test that unauthenticated users cannot resend invites."""
        org = OrganisationFactory()
        pending_invite = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=None,
        )

        url = reverse(
            "organisations:resend_invite",
            kwargs={"uuid": org.uuid, "member_uuid": pending_invite.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND

    def test_resend_shows_success_message(self, user: User, client):
        """Test that resending shows a success message with email."""
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
            "organisations:resend_invite",
            kwargs={"uuid": org.uuid, "member_uuid": pending_invite.uuid},
        )
        response = client.post(url, follow=True)

        assert response.status_code == HTTPStatus.OK
        messages = list(response.context["messages"])
        assert any("successfully resent" in str(m).lower() for m in messages)
        assert any("test@example.com" in str(m) for m in messages)

    def test_resend_sends_email(self, user: User, client):
        """Test that resending actually sends an email."""
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
            "organisations:resend_invite",
            kwargs={"uuid": org.uuid, "member_uuid": pending_invite.uuid},
        )

        # Clear any existing emails
        mail.outbox = []

        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        # Check that an email was sent
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["test@example.com"]

    def test_resend_updates_last_sent_datetime(self, user: User, client):
        """Test that resending updates the last_sent_datetime field."""
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
            last_sent_datetime=None,
        )

        client.force_login(user)
        url = reverse(
            "organisations:resend_invite",
            kwargs={"uuid": org.uuid, "member_uuid": pending_invite.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        pending_invite.refresh_from_db()
        assert pending_invite.last_sent_datetime is not None

    def test_resend_keeps_same_invite_token(self, user: User, client):
        """Test that resending keeps the same invite token (old link still works)."""
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
        original_token = pending_invite.invite_token

        client.force_login(user)
        url = reverse(
            "organisations:resend_invite",
            kwargs={"uuid": org.uuid, "member_uuid": pending_invite.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        pending_invite.refresh_from_db()
        # Token should remain unchanged
        assert pending_invite.invite_token == original_token

    def test_resend_does_not_delete_member(self, user: User, client):
        """Test that resending does not delete the member record (unlike revoke)."""
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
        pending_invite_id = pending_invite.id

        client.force_login(user)
        url = reverse(
            "organisations:resend_invite",
            kwargs={"uuid": org.uuid, "member_uuid": pending_invite.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        # Member record should still exist
        assert OrganisationMember.objects.filter(id=pending_invite_id).exists()
