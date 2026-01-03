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
class TestRevokeOrganisationAdminView:
    """Tests for RevokeOrganisationAdminView."""

    def test_org_admin_can_revoke_admin(self, user: User, client):
        """Test that an org admin can revoke admin status from another admin."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        admin_member = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse(
            "organisations:revoke_admin",
            kwargs={"uuid": org.uuid, "member_uuid": admin_member.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        admin_member.refresh_from_db()
        assert admin_member.role == OrganisationMember.Role.MEMBER

    def test_staff_can_revoke_admin(self, user: User, client):
        """Test that staff can revoke admin status."""
        user.is_staff = True
        user.save()

        org = OrganisationFactory()
        # Need at least one other admin
        OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        admin_member = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse(
            "organisations:revoke_admin",
            kwargs={"uuid": org.uuid, "member_uuid": admin_member.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        admin_member.refresh_from_db()
        assert admin_member.role == OrganisationMember.Role.MEMBER

    def test_cannot_revoke_yourself(self, user: User, client):
        """Test that you cannot revoke your own admin status."""
        org = OrganisationFactory()
        # Create another admin so we're not the last admin
        OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        admin_member = OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse(
            "organisations:revoke_admin",
            kwargs={"uuid": org.uuid, "member_uuid": admin_member.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.BAD_REQUEST
        admin_member.refresh_from_db()
        assert admin_member.role == OrganisationMember.Role.ADMIN

    def test_cannot_revoke_last_admin(self, user: User, client):
        """Test that the last admin's status cannot be revoked (using staff user)."""
        # Make user a staff member (not an org admin)
        user.is_staff = True
        user.save()

        org = OrganisationFactory()
        # Create only one admin
        the_only_admin = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)

        # Try to revoke the only admin's status (should fail)
        url = reverse(
            "organisations:revoke_admin",
            kwargs={"uuid": org.uuid, "member_uuid": the_only_admin.uuid},
        )
        response = client.post(url, follow=True)

        assert response.status_code == HTTPStatus.OK
        messages = list(response.context["messages"])
        assert any("last admin" in str(m).lower() for m in messages)
        the_only_admin.refresh_from_db()
        assert the_only_admin.role == OrganisationMember.Role.ADMIN

    def test_revoking_regular_member_shows_info_message(self, user: User, client):
        """Test that revoking a regular member shows info message."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        member = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse(
            "organisations:revoke_admin",
            kwargs={"uuid": org.uuid, "member_uuid": member.uuid},
        )
        response = client.post(url, follow=True)

        assert response.status_code == HTTPStatus.OK
        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "already a regular member" in str(messages[0])

    def test_non_admin_cannot_revoke_admin(self, user: User, client):
        """Test that non-admin members cannot revoke admin status."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        )
        admin_member = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse(
            "organisations:revoke_admin",
            kwargs={"uuid": org.uuid, "member_uuid": admin_member.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FORBIDDEN
        admin_member.refresh_from_db()
        assert admin_member.role == OrganisationMember.Role.ADMIN

    def test_non_member_cannot_revoke_admin(self, user: User, client):
        """Test that non-members cannot revoke admin status."""
        org = OrganisationFactory()
        admin_member = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse(
            "organisations:revoke_admin",
            kwargs={"uuid": org.uuid, "member_uuid": admin_member.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FORBIDDEN
        admin_member.refresh_from_db()
        assert admin_member.role == OrganisationMember.Role.ADMIN

    def test_unauthenticated_cannot_revoke_admin(self, client):
        """Test that unauthenticated users cannot revoke admin status."""
        org = OrganisationFactory()
        admin_member = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        url = reverse(
            "organisations:revoke_admin",
            kwargs={"uuid": org.uuid, "member_uuid": admin_member.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        admin_member.refresh_from_db()
        assert admin_member.role == OrganisationMember.Role.ADMIN
