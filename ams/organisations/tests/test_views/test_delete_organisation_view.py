from http import HTTPStatus

import pytest
from django.urls import reverse
from django.utils import timezone

from ams.memberships.models import OrganisationMembership
from ams.memberships.tests.factories import OrganisationMembershipFactory
from ams.organisations.models import Organisation
from ams.organisations.models import OrganisationMember
from ams.organisations.tests.factories import OrganisationFactory
from ams.organisations.tests.factories import OrganisationMemberFactory
from ams.users.models import User

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
class TestDeleteOrganisationView:
    """Tests for DeleteOrganisationView."""

    def test_only_member_can_delete_organisation(self, user: User, client):
        """Test that the only member can delete their organisation."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse("organisations:delete", kwargs={"uuid": org.uuid})
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        assert not Organisation.objects.filter(id=org.id).exists()

    def test_staff_cannot_delete_organisation_with_one_member(self, user: User, client):
        """Test that staff cannot delete an organisation with one member."""
        user.is_staff = True
        user.save()

        org = OrganisationFactory()
        # Create a different user as the only member
        OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse("organisations:delete", kwargs={"uuid": org.uuid})
        response = client.post(url, follow=True)

        # Should fail because the staff user is not a member
        assert response.status_code == HTTPStatus.OK
        messages = list(response.context["messages"])
        assert any("not a member" in str(m).lower() for m in messages)
        assert Organisation.objects.filter(id=org.id).exists()

    def test_cannot_delete_with_multiple_members(self, user: User, client):
        """Test that organisation cannot be deleted when multiple members exist."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        # Add another member
        OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse("organisations:delete", kwargs={"uuid": org.uuid})
        response = client.post(url, follow=True)

        assert response.status_code == HTTPStatus.OK
        messages = list(response.context["messages"])
        assert any("multiple members" in str(m).lower() for m in messages)
        assert Organisation.objects.filter(id=org.id).exists()

    def test_cannot_delete_if_not_member(self, user: User, client):
        """Test that non-members cannot delete an organisation."""
        org = OrganisationFactory()
        # Create another member
        OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse("organisations:delete", kwargs={"uuid": org.uuid})
        response = client.post(url)

        # Should fail permission check
        assert response.status_code == HTTPStatus.FORBIDDEN
        assert Organisation.objects.filter(id=org.id).exists()

    def test_unauthenticated_cannot_delete(self, client):
        """Test that unauthenticated users cannot delete organisations."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        url = reverse("organisations:delete", kwargs={"uuid": org.uuid})
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        assert Organisation.objects.filter(id=org.id).exists()

    def test_delete_redirects_to_user_detail(self, user: User, client):
        """Test that deleting redirects to user detail page."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse("organisations:delete", kwargs={"uuid": org.uuid})
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "users:detail",
            kwargs={"username": user.username},
        )

    def test_delete_shows_success_message(self, user: User, client):
        """Test that deleting shows a success message."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse("organisations:delete", kwargs={"uuid": org.uuid})
        response = client.post(url, follow=True)

        assert response.status_code == HTTPStatus.OK
        messages = list(response.context["messages"])
        assert any("successfully deleted" in str(m).lower() for m in messages)

    def test_declined_members_dont_prevent_deletion(self, user: User, client):
        """Test that declined members don't prevent deletion."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        # Add a declined member
        OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=None,
            declined_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse("organisations:delete", kwargs={"uuid": org.uuid})
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        assert not Organisation.objects.filter(id=org.id).exists()

    def test_pending_invites_prevent_deletion(self, user: User, client):
        """Test that pending invites prevent deletion."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        # Add a pending invite
        OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=None,
            declined_datetime=None,
        )

        client.force_login(user)
        url = reverse("organisations:delete", kwargs={"uuid": org.uuid})
        response = client.post(url, follow=True)

        assert response.status_code == HTTPStatus.OK
        messages = list(response.context["messages"])
        assert any("multiple members" in str(m).lower() for m in messages)
        assert Organisation.objects.filter(id=org.id).exists()

    def test_delete_cascades_to_members(self, user: User, client):
        """Test that deleting an organisation also deletes members."""
        org = OrganisationFactory()
        member = OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse("organisations:delete", kwargs={"uuid": org.uuid})
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        assert not Organisation.objects.filter(id=org.id).exists()
        assert not OrganisationMember.objects.filter(id=member.id).exists()

    def test_regular_member_as_only_member_cannot_delete(self, user: User, client):
        """Test that a regular member (not admin) cannot delete if they're the only
        member.

        This scenario should not be able to occur, as one admin must remain.
        """
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        )

        client.force_login(user)
        url = reverse("organisations:delete", kwargs={"uuid": org.uuid})
        response = client.post(url)

        # Should fail because regular member is not an admin
        assert response.status_code == HTTPStatus.FORBIDDEN
        assert Organisation.objects.filter(id=org.id).exists()

    def test_delete_with_memberships_cascades(self, user: User, client):
        """Test that deleting an organisation with memberships works (CASCADE)."""

        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        # Create a membership
        membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate(),
            expiry_date=timezone.localdate() + timezone.timedelta(days=365),
        )

        client.force_login(user)
        url = reverse("organisations:delete", kwargs={"uuid": org.uuid})
        response = client.post(url)

        assert response.status_code == HTTPStatus.FOUND
        assert not Organisation.objects.filter(id=org.id).exists()
        # Membership should also be deleted due to CASCADE

        assert not OrganisationMembership.objects.filter(id=membership.id).exists()
