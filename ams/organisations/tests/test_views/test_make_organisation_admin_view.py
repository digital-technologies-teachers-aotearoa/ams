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
class TestMakeOrganisationAdminView:
    """Tests for MakeOrganisationAdminView."""

    def test_org_admin_can_promote_member(self, user: User, client):
        """Test that an org admin can promote a member to admin."""
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
            "organisations:make_admin",
            kwargs={"uuid": org.uuid, "member_uuid": member.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        member.refresh_from_db()
        assert member.role == OrganisationMember.Role.ADMIN

    def test_staff_can_promote_member(self, user: User, client):
        """Test that staff can promote a member to admin."""
        user.is_staff = True
        user.save()

        org = OrganisationFactory()
        member = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse(
            "organisations:make_admin",
            kwargs={"uuid": org.uuid, "member_uuid": member.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        member.refresh_from_db()
        assert member.role == OrganisationMember.Role.ADMIN

    def test_cannot_promote_inactive_member(self, user: User, client):
        """Test that inactive members (pending invites) cannot be promoted."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        # Create a pending invite (not accepted)
        pending_member = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=None,
        )

        client.force_login(user)
        url = reverse(
            "organisations:make_admin",
            kwargs={"uuid": org.uuid, "member_uuid": pending_member.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.BAD_REQUEST
        pending_member.refresh_from_db()
        assert pending_member.role == OrganisationMember.Role.MEMBER

    def test_promoting_already_admin_shows_info_message(self, user: User, client):
        """Test that promoting an already-admin member shows info message."""
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
            "organisations:make_admin",
            kwargs={"uuid": org.uuid, "member_uuid": admin_member.uuid},
        )
        response = client.post(url, follow=True)

        assert response.status_code == HTTPStatus.OK
        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "already an admin" in str(messages[0])

    def test_non_admin_cannot_promote_member(self, user: User, client):
        """Test that non-admin members cannot promote other members."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        )
        other_member = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse(
            "organisations:make_admin",
            kwargs={"uuid": org.uuid, "member_uuid": other_member.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FORBIDDEN
        other_member.refresh_from_db()
        assert other_member.role == OrganisationMember.Role.MEMBER

    def test_non_member_cannot_promote_member(self, user: User, client):
        """Test that non-members cannot promote members."""
        org = OrganisationFactory()
        member = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse(
            "organisations:make_admin",
            kwargs={"uuid": org.uuid, "member_uuid": member.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FORBIDDEN
        member.refresh_from_db()
        assert member.role == OrganisationMember.Role.MEMBER

    def test_unauthenticated_cannot_promote_member(self, client):
        """Test that unauthenticated users cannot promote members."""
        org = OrganisationFactory()
        member = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        )

        url = reverse(
            "organisations:make_admin",
            kwargs={"uuid": org.uuid, "member_uuid": member.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        member.refresh_from_db()
        assert member.role == OrganisationMember.Role.MEMBER

    def test_cannot_promote_member_with_inactive_user(self, user: User, client):
        """Test that members with inactive user accounts cannot be promoted."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        # Create a member with an inactive user
        inactive_user = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        ).user
        inactive_user.is_active = False
        inactive_user.save()

        member = OrganisationMember.objects.get(user=inactive_user)

        client.force_login(user)
        url = reverse(
            "organisations:make_admin",
            kwargs={"uuid": org.uuid, "member_uuid": member.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.BAD_REQUEST
        member.refresh_from_db()
        assert member.role == OrganisationMember.Role.MEMBER
