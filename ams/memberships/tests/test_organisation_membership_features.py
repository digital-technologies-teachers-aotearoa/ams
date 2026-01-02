"""Tests for OrganisationMembership manager and properties."""

import pytest
from dateutil.relativedelta import relativedelta
from django.utils import timezone

from ams.memberships.models import MembershipOption
from ams.memberships.models import MembershipOptionType
from ams.memberships.models import OrganisationMembership
from ams.organisations.tests.factories import OrganisationFactory


@pytest.mark.django_db
class TestOrganisationMembershipManager:
    """Test OrganisationMembership manager methods."""

    def test_active_returns_only_active_memberships(self):
        """Test active() manager method returns only active memberships."""
        organisation = OrganisationFactory()
        membership_option = MembershipOption.objects.create(
            name="Annual",
            type=MembershipOptionType.ORGANISATION,
            duration=relativedelta(years=1),
            cost=1000,
            max_seats=10,
        )

        # Create active membership
        active = OrganisationMembership.objects.create(
            organisation=organisation,
            membership_option=membership_option,
            start_date=timezone.now().date() - relativedelta(days=30),
            expiry_date=timezone.now().date() + relativedelta(days=335),
            approved_datetime=timezone.now(),
            created_datetime=timezone.now(),
        )

        # Create expired membership
        OrganisationMembership.objects.create(
            organisation=organisation,
            membership_option=membership_option,
            start_date=timezone.now().date() - relativedelta(days=400),
            expiry_date=timezone.now().date() - relativedelta(days=35),
            approved_datetime=timezone.now(),
            created_datetime=timezone.now(),
        )

        # Create cancelled membership
        OrganisationMembership.objects.create(
            organisation=organisation,
            membership_option=membership_option,
            start_date=timezone.now().date() - relativedelta(days=30),
            expiry_date=timezone.now().date() + relativedelta(days=335),
            approved_datetime=timezone.now(),
            cancelled_datetime=timezone.now(),
            created_datetime=timezone.now(),
        )

        # Create future membership
        OrganisationMembership.objects.create(
            organisation=organisation,
            membership_option=membership_option,
            start_date=timezone.now().date() + relativedelta(days=30),
            expiry_date=timezone.now().date() + relativedelta(days=395),
            approved_datetime=timezone.now(),
            created_datetime=timezone.now(),
        )

        # Only active membership should be returned
        active_memberships = OrganisationMembership.objects.active()
        assert active_memberships.count() == 1
        assert active_memberships.first() == active


@pytest.mark.django_db
class TestOrganisationMembershipProperties:
    """Test OrganisationMembership seat-related properties."""

    def test_has_seat_limit_true_when_max_seats_set(self):
        """Test has_seat_limit returns True when max_seats is set."""
        organisation = OrganisationFactory()
        membership_option = MembershipOption.objects.create(
            name="Annual",
            type=MembershipOptionType.ORGANISATION,
            duration=relativedelta(years=1),
            cost=1000,
            max_seats=10,
        )
        membership = OrganisationMembership.objects.create(
            organisation=organisation,
            membership_option=membership_option,
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date() + relativedelta(years=1),
            approved_datetime=timezone.now(),
            created_datetime=timezone.now(),
            max_seats=10,  # Set max_seats on the membership instance
        )

        assert membership.has_seat_limit is True

    def test_has_seat_limit_false_when_no_limit(self):
        """Test has_seat_limit returns False when max_seats is None."""
        organisation = OrganisationFactory()
        membership_option = MembershipOption.objects.create(
            name="Unlimited",
            type=MembershipOptionType.ORGANISATION,
            duration=relativedelta(years=1),
            cost=1000,
            max_seats=None,
        )
        membership = OrganisationMembership.objects.create(
            organisation=organisation,
            membership_option=membership_option,
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date() + relativedelta(years=1),
            approved_datetime=timezone.now(),
            created_datetime=timezone.now(),
        )

        assert membership.has_seat_limit is False

    def test_seats_available_calculates_correctly(self):
        """Test seats_available returns correct number."""
        organisation = OrganisationFactory()
        membership_option = MembershipOption.objects.create(
            name="Annual",
            type=MembershipOptionType.ORGANISATION,
            duration=relativedelta(years=1),
            cost=1000,
            max_seats=10,
        )
        membership = OrganisationMembership.objects.create(
            organisation=organisation,
            membership_option=membership_option,
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date() + relativedelta(years=1),
            approved_datetime=timezone.now(),
            created_datetime=timezone.now(),
            max_seats=10,  # Set max_seats on the membership instance
        )

        # With 0 occupied seats, should have 10 available
        assert membership.seats_available == 10  # noqa: PLR2004

    def test_seats_available_returns_none_when_no_limit(self):
        """Test seats_available returns None when no seat limit."""
        organisation = OrganisationFactory()
        membership_option = MembershipOption.objects.create(
            name="Unlimited",
            type=MembershipOptionType.ORGANISATION,
            duration=relativedelta(years=1),
            cost=1000,
            max_seats=None,
        )
        membership = OrganisationMembership.objects.create(
            organisation=organisation,
            membership_option=membership_option,
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date() + relativedelta(years=1),
            approved_datetime=timezone.now(),
            created_datetime=timezone.now(),
        )

        assert membership.seats_available is None

    def test_is_full_false_when_seats_available(self):
        """Test is_full returns False when seats are available."""
        organisation = OrganisationFactory()
        membership_option = MembershipOption.objects.create(
            name="Annual",
            type=MembershipOptionType.ORGANISATION,
            duration=relativedelta(years=1),
            cost=1000,
            max_seats=10,
        )
        membership = OrganisationMembership.objects.create(
            organisation=organisation,
            membership_option=membership_option,
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date() + relativedelta(years=1),
            approved_datetime=timezone.now(),
            created_datetime=timezone.now(),
        )

        assert membership.is_full is False

    def test_is_full_false_when_no_seat_limit(self):
        """Test is_full returns False when there's no seat limit."""
        organisation = OrganisationFactory()
        membership_option = MembershipOption.objects.create(
            name="Unlimited",
            type=MembershipOptionType.ORGANISATION,
            duration=relativedelta(years=1),
            cost=1000,
            max_seats=None,
        )

        membership = OrganisationMembership.objects.create(
            organisation=organisation,
            membership_option=membership_option,
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date() + relativedelta(years=1),
            approved_datetime=timezone.now(),
            created_datetime=timezone.now(),
        )

        assert membership.is_full is False
