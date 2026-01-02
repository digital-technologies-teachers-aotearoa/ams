from datetime import timedelta
from http import HTTPStatus

import pytest
from django.urls import reverse
from django.utils import timezone

from ams.memberships.models import MembershipOptionType
from ams.memberships.tests.factories import OrganisationMembershipFactory
from ams.organisations.models import OrganisationMember
from ams.organisations.tests.factories import OrganisationFactory
from ams.organisations.tests.factories import OrganisationMemberFactory
from ams.users.models import User

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
class TestOrganisationDetailView:
    """Tests for OrganisationDetailView with focus on active membership detection."""

    def test_active_membership_current(self, user: User, client):
        """Test that a current active membership is correctly identified."""

        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        client.force_login(user)

        # Create an active membership (started 30 days ago, expires in 335 days)
        active_membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=335),
            cancelled_datetime=None,
            membership_option__type=MembershipOptionType.ORGANISATION,
            membership_option__max_seats=10,
        )

        url = reverse("organisations:detail", kwargs={"uuid": org.uuid})
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.context["active_membership"] == active_membership
        assert response.context["seat_limit"] == int(
            active_membership.membership_option.max_seats,
        )
        assert response.context["occupied_seats"] == active_membership.occupied_seats

    def test_expired_membership_not_active(self, user: User, client):
        """Test that an expired membership is not considered active."""

        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        client.force_login(user)

        # Create an expired membership (expired yesterday)
        OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate() - timedelta(days=365),
            expiry_date=timezone.localdate() - timedelta(days=1),
            cancelled_datetime=None,
        )

        url = reverse("organisations:detail", kwargs={"uuid": org.uuid})
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.context["active_membership"] is None
        assert response.context["seat_limit"] is None
        assert response.context["occupied_seats"] == 0

    def test_future_membership_not_active(self, user: User, client):
        """Test that a future membership is not considered active."""

        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        client.force_login(user)

        # Create a future membership (starts tomorrow)
        OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate() + timedelta(days=1),
            expiry_date=timezone.localdate() + timedelta(days=366),
            cancelled_datetime=None,
        )

        url = reverse("organisations:detail", kwargs={"uuid": org.uuid})
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.context["active_membership"] is None
        assert response.context["seat_limit"] is None
        assert response.context["occupied_seats"] == 0

    def test_cancelled_membership_not_active(self, user: User, client):
        """Test that a cancelled membership is not considered active."""

        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        client.force_login(user)

        # Create a cancelled membership (would be active otherwise)
        OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=335),
            cancelled_datetime=timezone.now(),
        )

        url = reverse("organisations:detail", kwargs={"uuid": org.uuid})
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.context["active_membership"] is None
        assert response.context["seat_limit"] is None
        assert response.context["occupied_seats"] == 0

    def test_multiple_memberships_only_active_shown(self, user: User, client):
        """Test that only the active membership is shown when multiple exist."""

        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        client.force_login(user)

        # Create past membership
        OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate() - timedelta(days=730),
            expiry_date=timezone.localdate() - timedelta(days=365),
            cancelled_datetime=None,
        )

        # Create active membership
        active_membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=335),
            cancelled_datetime=None,
            membership_option__type=MembershipOptionType.ORGANISATION,
            membership_option__max_seats=10,
        )

        # Create future membership
        OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate() + timedelta(days=335),
            expiry_date=timezone.localdate() + timedelta(days=700),
            cancelled_datetime=None,
        )

        url = reverse("organisations:detail", kwargs={"uuid": org.uuid})
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.context["active_membership"] == active_membership
        assert response.context["seat_limit"] == int(
            active_membership.membership_option.max_seats,
        )
        assert response.context["occupied_seats"] == active_membership.occupied_seats

    def test_no_membership(self, user: User, client):
        """Test that organisations without memberships show no active membership."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        client.force_login(user)

        url = reverse("organisations:detail", kwargs={"uuid": org.uuid})
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.context["active_membership"] is None
        assert response.context["seat_limit"] is None
        assert response.context["occupied_seats"] == 0

    def test_membership_starting_today(self, user: User, client):
        """Test that a membership starting today is considered active."""

        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        client.force_login(user)

        # Create a membership starting today
        active_membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate(),
            expiry_date=timezone.localdate() + timedelta(days=365),
            cancelled_datetime=None,
        )

        url = reverse("organisations:detail", kwargs={"uuid": org.uuid})
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.context["active_membership"] == active_membership

    def test_membership_expiring_tomorrow(self, user: User, client):
        """Test that a membership expiring tomorrow is considered active."""

        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        client.force_login(user)

        # Create a membership expiring today
        active_membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate() - timedelta(days=365),
            expiry_date=timezone.localdate() + timedelta(days=1),
            cancelled_datetime=None,
        )

        url = reverse("organisations:detail", kwargs={"uuid": org.uuid})
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.context["active_membership"] == active_membership

    def test_membership_expiring_today(self, user: User, client):
        """Test that a membership expiring today is considered expired."""

        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        client.force_login(user)

        # Create a membership expiring today
        OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate() - timedelta(days=365),
            expiry_date=timezone.localdate(),
            cancelled_datetime=None,
        )

        url = reverse("organisations:detail", kwargs={"uuid": org.uuid})
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.context["active_membership"] is None

    def test_declined_invites_not_in_member_list(self, user: User, client):
        """Test that declined invites are excluded from the member list."""

        org = OrganisationFactory()
        # Admin user
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        client.force_login(user)

        # Create an accepted member
        accepted_member = OrganisationMemberFactory(
            organisation=org,
            accepted_datetime=timezone.now(),
        )

        # Create a pending invite
        pending_member = OrganisationMemberFactory(
            organisation=org,
            accepted_datetime=None,
            declined_datetime=None,
        )

        # Create a declined invite
        declined_member = OrganisationMemberFactory(
            organisation=org,
            accepted_datetime=None,
            declined_datetime=timezone.now(),
        )

        url = reverse("organisations:detail", kwargs={"uuid": org.uuid})
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK

        # Get the member table data
        member_table = response.context["member_table"]
        member_ids = [member.id for member in member_table.data]

        # Accepted and pending members should be in the list
        assert user.organisation_members.first().id in member_ids
        assert accepted_member.id in member_ids
        assert pending_member.id in member_ids

        # Declined member should NOT be in the list
        assert declined_member.id not in member_ids
