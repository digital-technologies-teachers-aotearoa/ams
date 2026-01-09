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

        url = reverse("organisations:invite_member", kwargs={"uuid": org.uuid})
        data = {"email": "newmember@example.com"}

        response = client.post(url, data=data)

        # Should redirect to organisation detail
        assert response.status_code == HTTPStatus.FOUND
        assert f"/organisations/{org.uuid}/" in response.url

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

        url = reverse("organisations:invite_member", kwargs={"uuid": org.uuid})
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
        url = reverse("organisations:invite_member", kwargs={"uuid": org.uuid})
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

        url = reverse("organisations:invite_member", kwargs={"uuid": org.uuid})
        response = client.get(url)

        # Should be forbidden
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_invite_member_not_authenticated(self, client):
        """Test that unauthenticated users cannot invite."""
        org = OrganisationFactory()
        url = reverse("organisations:invite_member", kwargs={"uuid": org.uuid})

        response = client.get(url)

        # Should redirect to login
        assert response.status_code == HTTPStatus.FOUND
        assert "/accounts/login/" in response.url

    def test_invite_allowed_when_no_existing_record(
        self,
        user: User,
        client,
        mailoutbox,
    ):
        """Test that inviting works when there's no existing invite record.

        Note: In production, declined/revoked invites are deleted immediately,
        so there won't be any conflicting records when re-inviting.
        """
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse("organisations:invite_member", kwargs={"uuid": org.uuid})
        data = {"email": "newuser@example.com"}

        response = client.post(url, data=data)

        # Should redirect to organisation detail (successful invite)
        assert response.status_code == HTTPStatus.FOUND
        assert f"/organisations/{org.uuid}/" in response.url

        # New invite should be created
        new_member = OrganisationMember.objects.get(
            organisation=org,
            invite_email="newuser@example.com",
        )
        assert new_member.accepted_datetime is None
        assert new_member.declined_datetime is None
        assert new_member.revoked_datetime is None

        # Email should be sent
        assert len(mailoutbox) == 1
        assert mailoutbox[0].to == ["newuser@example.com"]
