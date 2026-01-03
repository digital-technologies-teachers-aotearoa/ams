from http import HTTPStatus

import pytest
from django.urls import reverse
from django.utils import timezone

from ams.memberships.tests.factories import OrganisationMembershipFactory
from ams.organisations.models import OrganisationMember
from ams.organisations.tests.factories import OrganisationFactory
from ams.organisations.tests.factories import OrganisationMemberFactory
from ams.users.models import User

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
class TestRemoveOrganisationMemberView:
    """Tests for RemoveOrganisationMemberView."""

    def test_org_admin_can_remove_regular_member(self, user: User, client):
        """Test that an org admin can remove a regular member."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        regular_member = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse(
            "organisations:remove_member",
            kwargs={"uuid": org.uuid, "member_uuid": regular_member.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        assert not OrganisationMember.objects.filter(id=regular_member.id).exists()

    def test_staff_can_remove_member(self, user: User, client):
        """Test that staff can remove a member."""
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
            "organisations:remove_member",
            kwargs={"uuid": org.uuid, "member_uuid": member.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        assert not OrganisationMember.objects.filter(id=member.id).exists()

    def test_cannot_remove_yourself(self, user: User, client):
        """Test that you cannot remove yourself through this action."""
        org = OrganisationFactory()
        member = OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse(
            "organisations:remove_member",
            kwargs={"uuid": org.uuid, "member_uuid": member.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert OrganisationMember.objects.filter(id=member.id).exists()

    def test_cannot_remove_last_admin(self, user: User, client):
        """Test that the last admin cannot be removed (using staff user)."""
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

        # Try to remove the only admin (should fail)
        url = reverse(
            "organisations:remove_member",
            kwargs={"uuid": org.uuid, "member_uuid": the_only_admin.uuid},
        )
        response = client.post(url, follow=True)

        # Should redirect with error message
        assert response.status_code == HTTPStatus.OK
        messages = list(response.context["messages"])
        assert any("last admin" in str(m).lower() for m in messages)
        # Admin should still exist
        assert OrganisationMember.objects.filter(id=the_only_admin.id).exists()

    def test_non_admin_cannot_remove_member(self, user: User, client):
        """Test that non-admin members cannot remove other members."""
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
            "organisations:remove_member",
            kwargs={"uuid": org.uuid, "member_uuid": other_member.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert OrganisationMember.objects.filter(id=other_member.id).exists()

    def test_non_member_cannot_remove_member(self, user: User, client):
        """Test that non-members cannot remove members."""
        org = OrganisationFactory()
        member = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse(
            "organisations:remove_member",
            kwargs={"uuid": org.uuid, "member_uuid": member.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert OrganisationMember.objects.filter(id=member.id).exists()

    def test_unauthenticated_cannot_remove_member(self, client):
        """Test that unauthenticated users cannot remove members."""
        org = OrganisationFactory()
        member = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        )

        url = reverse(
            "organisations:remove_member",
            kwargs={"uuid": org.uuid, "member_uuid": member.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        assert OrganisationMember.objects.filter(id=member.id).exists()

    def test_removing_member_frees_seat(self, user: User, client):
        """Test that removing a member frees a seat immediately."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        # Create active membership
        membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate(),
            expiry_date=timezone.localdate() + timezone.timedelta(days=365),
            cancelled_datetime=None,
        )

        # Create an accepted member
        member = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        )

        # Check occupied seats before removal
        occupied_before = membership.occupied_seats

        client.force_login(user)
        url = reverse(
            "organisations:remove_member",
            kwargs={"uuid": org.uuid, "member_uuid": member.uuid},
        )
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND

        # Refresh membership to get updated occupied seats
        membership.refresh_from_db()
        assert membership.occupied_seats == occupied_before - 1
