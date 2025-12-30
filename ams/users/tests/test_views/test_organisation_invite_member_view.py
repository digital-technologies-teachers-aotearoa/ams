from http import HTTPStatus

import pytest
from django.urls import reverse
from django.utils import timezone

from ams.users.models import OrganisationMember
from ams.users.models import User
from ams.users.tests.factories import OrganisationFactory
from ams.users.tests.factories import OrganisationMemberFactory
from ams.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
class TestOrganisationInviteMemberView:
    """Tests for the OrganisationInviteMemberView"""

    def test_invite_member_as_org_admin(self, user: User, client, mailoutbox):
        """Test that organisation admins can invite members."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        client.force_login(user)

        url = reverse("users:organisation_invite_member", kwargs={"uuid": org.uuid})
        data = {"email": "newmember@example.com"}

        response = client.post(url, data=data)

        # Should redirect to organisation detail
        assert response.status_code == HTTPStatus.FOUND
        assert f"/users/organisations/view/{org.uuid}/" in response.url

        # Member invite should be created
        member = OrganisationMember.objects.get(
            organisation=org,
            invite_email="newmember@example.com",
        )
        assert member.user is None  # No user yet
        assert member.accepted_datetime is None
        assert member.role == OrganisationMember.Role.MEMBER

        # Email should be sent
        assert len(mailoutbox) == 1
        assert mailoutbox[0].to == ["newmember@example.com"]
        assert org.name in mailoutbox[0].subject

    def test_invite_existing_user(self, user: User, client, mailoutbox):
        """Test inviting an email that belongs to an existing user."""
        existing_user = UserFactory(email="existing@example.com")
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        client.force_login(user)

        url = reverse("users:organisation_invite_member", kwargs={"uuid": org.uuid})
        data = {"email": "existing@example.com"}

        response = client.post(url, data=data)

        assert response.status_code == HTTPStatus.FOUND

        # Member invite should be created with user link
        member = OrganisationMember.objects.get(
            organisation=org,
            invite_email="existing@example.com",
        )
        assert member.user == existing_user
        assert member.accepted_datetime is None

        # Email should be sent
        assert len(mailoutbox) == 1
        assert mailoutbox[0].to == ["existing@example.com"]

    def test_invite_duplicate_email_rejected(self, user: User, client):
        """Test that inviting a duplicate email is rejected."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        # Create an existing member
        OrganisationMemberFactory(
            organisation=org,
            invite_email="duplicate@example.com",
        )

        client.force_login(user)
        url = reverse("users:organisation_invite_member", kwargs={"uuid": org.uuid})
        data = {"email": "duplicate@example.com"}

        response = client.post(url, data=data)

        # Should not redirect (form invalid)
        assert response.status_code == HTTPStatus.OK
        assert "already associated with a member" in response.content.decode()

    def test_invite_member_not_org_admin(self, user: User, client):
        """Test that non-admin members cannot invite."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.MEMBER,  # Not admin
            accepted_datetime=timezone.now(),
        )
        client.force_login(user)

        url = reverse("users:organisation_invite_member", kwargs={"uuid": org.uuid})
        response = client.get(url)

        # Should be forbidden
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_invite_member_not_authenticated(self, client):
        """Test that unauthenticated users cannot invite."""
        org = OrganisationFactory()
        url = reverse("users:organisation_invite_member", kwargs={"uuid": org.uuid})

        response = client.get(url)

        # Should redirect to login
        assert response.status_code == HTTPStatus.FOUND
        assert "/accounts/login/" in response.url

    def test_reinvite_declined_user(self, user: User, client, mailoutbox):
        """Test that users who declined an invite can be re-invited."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        # Create a declined invite
        declined_member = OrganisationMemberFactory(
            organisation=org,
            invite_email="declined@example.com",
            accepted_datetime=None,
            declined_datetime=timezone.now(),
        )
        declined_member_id = declined_member.id

        client.force_login(user)
        url = reverse("users:organisation_invite_member", kwargs={"uuid": org.uuid})
        data = {"email": "declined@example.com"}

        response = client.post(url, data=data)

        # Should redirect to organisation detail (successful invite)
        assert response.status_code == HTTPStatus.FOUND
        assert f"/users/organisations/view/{org.uuid}/" in response.url

        # Old declined invite should still exist (not deleted)
        assert OrganisationMember.objects.filter(id=declined_member_id).exists()
        old_invite = OrganisationMember.objects.get(id=declined_member_id)
        assert old_invite.declined_datetime is not None

        # New invite should be created
        new_member = OrganisationMember.objects.get(
            organisation=org,
            invite_email="declined@example.com",
            declined_datetime__isnull=True,
        )
        assert new_member.accepted_datetime is None
        assert new_member.id != declined_member_id  # Different member record

        # Should have 2 total invites for this email (1 declined, 1 pending)
        assert (
            OrganisationMember.objects.filter(
                organisation=org,
                invite_email="declined@example.com",
            ).count()
            == 2  # noqa: PLR2004
        )

        # Email should be sent
        assert len(mailoutbox) == 1
        assert mailoutbox[0].to == ["declined@example.com"]

    def test_reinvite_declined_existing_user(self, user: User, client, mailoutbox):
        """Test re-inviting an existing user who previously declined."""
        existing_user = UserFactory(email="existing@example.com")
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        # Create a declined invite with user linked
        declined_member = OrganisationMemberFactory(
            organisation=org,
            user=existing_user,
            invite_email="existing@example.com",
            accepted_datetime=None,
            declined_datetime=timezone.now(),
        )
        declined_member_id = declined_member.id

        client.force_login(user)
        url = reverse("users:organisation_invite_member", kwargs={"uuid": org.uuid})
        data = {"email": "existing@example.com"}

        response = client.post(url, data=data)

        # Should redirect to organisation detail (successful invite)
        assert response.status_code == HTTPStatus.FOUND

        # Old declined invite should still exist (not deleted)
        assert OrganisationMember.objects.filter(id=declined_member_id).exists()
        old_invite = OrganisationMember.objects.get(id=declined_member_id)
        assert old_invite.declined_datetime is not None

        # New invite should be created with user linked
        new_member = OrganisationMember.objects.get(
            organisation=org,
            invite_email="existing@example.com",
            declined_datetime__isnull=True,
        )
        assert new_member.user == existing_user
        assert new_member.accepted_datetime is None
        assert new_member.id != declined_member_id  # Different member record

        # Should have 2 total invites for this user+org (1 declined, 1 pending)
        assert (
            OrganisationMember.objects.filter(
                organisation=org,
                user=existing_user,
            ).count()
            == 2  # noqa: PLR2004
        )

        # Email should be sent
        assert len(mailoutbox) == 1
        assert mailoutbox[0].to == ["existing@example.com"]
