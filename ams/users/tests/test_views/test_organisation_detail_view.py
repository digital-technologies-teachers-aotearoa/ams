from datetime import timedelta
from http import HTTPStatus

import pytest
from django.urls import reverse
from django.utils import timezone

from ams.memberships.models import MembershipOptionType
from ams.memberships.tests.factories import OrganisationMembershipFactory
from ams.users.models import OrganisationMember
from ams.users.models import User
from ams.users.tests.factories import OrganisationFactory
from ams.users.tests.factories import OrganisationMemberFactory

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
            start_date=timezone.now().date() - timedelta(days=30),
            expiry_date=timezone.now().date() + timedelta(days=335),
            cancelled_datetime=None,
            membership_option__type=MembershipOptionType.ORGANISATION,
            membership_option__max_seats=10,
        )

        url = reverse("users:organisation_detail", kwargs={"uuid": org.uuid})
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
            start_date=timezone.now().date() - timedelta(days=365),
            expiry_date=timezone.now().date() - timedelta(days=1),
            cancelled_datetime=None,
        )

        url = reverse("users:organisation_detail", kwargs={"uuid": org.uuid})
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
            start_date=timezone.now().date() + timedelta(days=1),
            expiry_date=timezone.now().date() + timedelta(days=366),
            cancelled_datetime=None,
        )

        url = reverse("users:organisation_detail", kwargs={"uuid": org.uuid})
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
            start_date=timezone.now().date() - timedelta(days=30),
            expiry_date=timezone.now().date() + timedelta(days=335),
            cancelled_datetime=timezone.now(),
        )

        url = reverse("users:organisation_detail", kwargs={"uuid": org.uuid})
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
            start_date=timezone.now().date() - timedelta(days=730),
            expiry_date=timezone.now().date() - timedelta(days=365),
            cancelled_datetime=None,
        )

        # Create active membership
        active_membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.now().date() - timedelta(days=30),
            expiry_date=timezone.now().date() + timedelta(days=335),
            cancelled_datetime=None,
            membership_option__type=MembershipOptionType.ORGANISATION,
            membership_option__max_seats=10,
        )

        # Create future membership
        OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.now().date() + timedelta(days=335),
            expiry_date=timezone.now().date() + timedelta(days=700),
            cancelled_datetime=None,
        )

        url = reverse("users:organisation_detail", kwargs={"uuid": org.uuid})
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

        url = reverse("users:organisation_detail", kwargs={"uuid": org.uuid})
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
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timedelta(days=365),
            cancelled_datetime=None,
        )

        url = reverse("users:organisation_detail", kwargs={"uuid": org.uuid})
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.context["active_membership"] == active_membership

    def test_membership_expiring_today(self, user: User, client):
        """Test that a membership expiring today is still considered active."""

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
            start_date=timezone.now().date() - timedelta(days=365),
            expiry_date=timezone.now().date(),
            cancelled_datetime=None,
        )

        url = reverse("users:organisation_detail", kwargs={"uuid": org.uuid})
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert response.context["active_membership"] == active_membership
