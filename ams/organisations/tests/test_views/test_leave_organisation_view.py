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
class TestLeaveOrganisationView:
    """Tests for LeaveOrganisationView."""

    def test_regular_member_can_leave(self, user: User, client):
        """Test that a regular member can leave an organisation."""
        org = OrganisationFactory()
        # Create an admin (not the user)
        OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        # Create the user as a regular member
        member = OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse("organisations:leave", kwargs={"uuid": org.uuid})
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        assert not OrganisationMember.objects.filter(id=member.id).exists()

    def test_admin_can_leave_if_not_last_admin(self, user: User, client):
        """Test that an admin can leave if there's another admin."""
        org = OrganisationFactory()
        # Create another admin
        OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        # Create the user as an admin
        member = OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse("organisations:leave", kwargs={"uuid": org.uuid})
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        assert not OrganisationMember.objects.filter(id=member.id).exists()

    def test_last_admin_cannot_leave(self, user: User, client):
        """Test that the last admin cannot leave."""
        org = OrganisationFactory()
        member = OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse("organisations:leave", kwargs={"uuid": org.uuid})
        response = client.post(url, follow=True)

        assert response.status_code == HTTPStatus.OK
        messages = list(response.context["messages"])
        assert any("last admin" in str(m) for m in messages)
        assert OrganisationMember.objects.filter(id=member.id).exists()

    def test_non_member_cannot_leave(self, user: User, client):
        """Test that non-members cannot leave an organisation."""
        org = OrganisationFactory()

        client.force_login(user)
        url = reverse("organisations:leave", kwargs={"uuid": org.uuid})
        response = client.post(url)

        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_unauthenticated_cannot_leave(self, client):
        """Test that unauthenticated users cannot leave."""
        org = OrganisationFactory()

        url = reverse("organisations:leave", kwargs={"uuid": org.uuid})
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND

    def test_leaving_redirects_to_user_detail(self, user: User, client):
        """Test that leaving redirects to user detail page."""
        org = OrganisationFactory()
        # Create an admin (not the user)
        OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        # Create the user as a regular member
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse("organisations:leave", kwargs={"uuid": org.uuid})
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "users:detail",
            kwargs={"username": user.username},
        )

    def test_leaving_frees_seat_immediately(self, user: User, client):
        """Test that leaving an organisation frees a seat immediately."""
        org = OrganisationFactory()
        # Create an admin (not the user)
        OrganisationMemberFactory(
            organisation=org,
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

        # Create the user as a regular member
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        )

        # Check occupied seats before leaving
        occupied_before = membership.occupied_seats

        client.force_login(user)
        url = reverse("organisations:leave", kwargs={"uuid": org.uuid})
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND

        # Refresh membership to get updated occupied seats
        membership.refresh_from_db()
        assert membership.occupied_seats == occupied_before - 1

    def test_declined_member_cannot_leave(self, user: User, client):
        """Test that members who declined an invite cannot leave."""
        org = OrganisationFactory()
        # Create a declined membership
        member = OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=None,
            declined_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse("organisations:leave", kwargs={"uuid": org.uuid})
        response = client.post(url)

        assert response.status_code == HTTPStatus.BAD_REQUEST
        # Member should still exist
        assert OrganisationMember.objects.filter(id=member.id).exists()
