"""Tests for OrganisationMembership manager and properties."""

from datetime import timedelta

import pytest
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.utils import timezone

from ams.memberships.models import MembershipOption
from ams.memberships.models import MembershipOptionType
from ams.memberships.models import MembershipStatus
from ams.memberships.models import OrganisationMembership
from ams.memberships.tests.factories import OrganisationMembershipFactory
from ams.organisations.models import OrganisationMember
from ams.organisations.tests.factories import OrganisationFactory
from ams.organisations.tests.factories import OrganisationMemberFactory
from ams.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


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
            seats=1,
        )

        # Create expired membership
        OrganisationMembership.objects.create(
            organisation=organisation,
            membership_option=membership_option,
            start_date=timezone.now().date() - relativedelta(days=400),
            expiry_date=timezone.now().date() - relativedelta(days=35),
            approved_datetime=timezone.now(),
            created_datetime=timezone.now(),
            seats=1,
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
            seats=1,
        )

        # Create future membership
        OrganisationMembership.objects.create(
            organisation=organisation,
            membership_option=membership_option,
            start_date=timezone.now().date() + relativedelta(days=30),
            expiry_date=timezone.now().date() + relativedelta(days=395),
            approved_datetime=timezone.now(),
            created_datetime=timezone.now(),
            seats=1,
        )

        # Only active membership should be returned
        active_memberships = OrganisationMembership.objects.active()
        assert active_memberships.count() == 1
        assert active_memberships.first() == active


class TestOrganisationMembership:
    def test_str(self):
        # Arrange
        membership = OrganisationMembershipFactory()
        # Act
        result = str(membership)
        # Assert
        assert membership.organisation.name in result
        assert membership.membership_option.name in result
        assert "Status:" in result

    def test_clean_expiry_before_start_raises(self):
        # Arrange
        membership = OrganisationMembershipFactory()
        membership.start_date = timezone.localdate()
        membership.expiry_date = membership.start_date - timedelta(days=1)
        # Act & Assert
        with pytest.raises(ValidationError) as exc:
            membership.clean()
        assert "Expiry date must be after start date." in str(exc.value)

    def test_is_expired(self):
        # Arrange
        membership = OrganisationMembershipFactory(expired=True)
        # Act
        result = membership.is_expired()
        # Assert
        assert result is True

    def test_is_expired_with_none_expiry_date(self):
        # Arrange
        membership = OrganisationMembershipFactory()
        membership.expiry_date = None
        # Act
        result = membership.is_expired()
        # Assert - membership without expiry_date should not be considered expired
        assert result is False

    def test_membership_expiring_tomorrow_is_not_expired(self):
        # Arrange
        today = timezone.localdate()
        membership = OrganisationMembershipFactory(
            start_date=today - timedelta(days=365),
            expiry_date=today + timedelta(days=1),
            approved_datetime=timezone.now(),
            cancelled_datetime=None,
        )
        # Act
        result = membership.is_expired()
        # Assert - membership expiring tomorrow should not be expired
        assert result is False

    def test_membership_expiring_today_is_expired(self):
        # Arrange
        today = timezone.localdate()
        membership = OrganisationMembershipFactory(
            start_date=today - timedelta(days=365),
            expiry_date=today,
            approved_datetime=timezone.now(),
            cancelled_datetime=None,
        )
        # Act
        result = membership.is_expired()
        # Assert - membership expiring today should be expired
        assert result is True

    def test_status_cancelled(self):
        # Arrange
        membership = OrganisationMembershipFactory(cancelled=True)
        # Act
        status = membership.status()
        # Assert
        assert status == MembershipStatus.CANCELLED

    def test_status_expired(self):
        # Arrange
        membership = OrganisationMembershipFactory(
            expired=True,
        )
        # Act
        status = membership.status()
        # Assert
        assert status == MembershipStatus.EXPIRED

    def test_status_active(self):
        # Arrange
        membership = OrganisationMembershipFactory(active=True)
        # Act
        status = membership.status()
        # Assert
        assert status == MembershipStatus.ACTIVE

    def test_calculate_expiry_date(self):
        # Arrange
        membership = OrganisationMembershipFactory()
        # Act
        calculated = membership.calculate_expiry_date()
        # Assert
        assert calculated == (
            membership.start_date + membership.membership_option.duration
        )

    def test_occupied_seats_active_membership(self):
        # Arrange
        membership = OrganisationMembershipFactory(active=True)
        # Create 3 accepted, active members
        OrganisationMemberFactory.create_batch(
            3,
            organisation=membership.organisation,
            accepted_datetime=timezone.now(),
            user__is_active=True,
        )
        # Create 1 pending invite (not accepted)
        OrganisationMemberFactory(
            organisation=membership.organisation,
            accepted_datetime=None,
        )
        # Create 1 accepted but inactive user
        OrganisationMemberFactory(
            organisation=membership.organisation,
            accepted_datetime=timezone.now(),
            user__is_active=False,
        )
        # Act
        seats = membership.occupied_seats
        # Assert - only the 3 accepted + active should count
        assert seats == 3  # noqa: PLR2004

    def test_occupied_seats_pending_membership_counts(self):
        # Arrange - pending membership (not yet approved)
        membership = OrganisationMembershipFactory(pending=True)
        # Create 2 accepted, active members
        OrganisationMemberFactory.create_batch(
            2,
            organisation=membership.organisation,
            accepted_datetime=timezone.now(),
            user__is_active=True,
        )
        # Act
        seats = membership.occupied_seats
        # Assert - pending membership should count occupied seats
        expected_seats = 2
        assert seats == expected_seats

    def test_occupied_seats_expired_membership_returns_zero(self):
        # Arrange
        membership = OrganisationMembershipFactory(expired=True)
        # Create accepted, active members
        OrganisationMemberFactory.create_batch(
            5,
            organisation=membership.organisation,
            accepted_datetime=timezone.now(),
            user__is_active=True,
        )
        # Act
        seats = membership.occupied_seats
        # Assert - expired membership shows 0 occupied seats
        assert seats == 0

    def test_occupied_seats_cancelled_membership_returns_zero(self):
        # Arrange
        membership = OrganisationMembershipFactory(cancelled=True)
        # Create accepted, active members
        OrganisationMemberFactory.create_batch(
            2,
            organisation=membership.organisation,
            accepted_datetime=timezone.now(),
            user__is_active=True,
        )
        # Act
        seats = membership.occupied_seats
        # Assert - cancelled membership shows 0 occupied seats
        assert seats == 0

    def test_occupied_seats_no_members(self):
        # Arrange
        membership = OrganisationMembershipFactory(active=True)
        # Act
        seats = membership.occupied_seats
        # Assert
        assert seats == 0


class TestOrganisationMembershipHasSeatLimit:
    def test_has_seat_limit_true_when_max_seats_set(self):
        """Test has_seat_limit returns True when seats is set."""
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
            seats=10,  # Set seats on the membership instance
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
            seats=1,
        )

        assert membership.has_seat_limit is False


class TestOrganisationMembershipSeatsAvailable:
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
            seats=10,  # Set seats on the membership instance
        )

        # With 0 occupied seats, should have 10 available
        assert membership.seats_available == 10  # noqa: PLR2004


class TestOrganisationMembershipIsFull:
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
            seats=5,
        )

        assert membership.is_full is False


class TestOrganisationMembershipSeatsSummary:
    def test_shows_limit_when_max_seats_set(self):
        org = OrganisationFactory()
        option = MembershipOption.objects.create(
            name="Annual",
            type=MembershipOptionType.ORGANISATION,
            duration=relativedelta(years=1),
            cost=1000,
            max_seats=5,
        )

        membership = OrganisationMembership.objects.create(
            organisation=org,
            membership_option=option,
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date() + relativedelta(years=1),
            approved_datetime=timezone.now(),
            created_datetime=timezone.now(),
            seats=5,
        )

        # No occupied members yet
        assert membership.occupied_seats == 0
        assert "Membership has limit of 5 seats" in membership.seats_summary()

    def test_shows_simple_summary_when_no_limit(self):
        org = OrganisationFactory()
        option = MembershipOption.objects.create(
            name="Unlimited",
            type=MembershipOptionType.ORGANISATION,
            duration=relativedelta(years=1),
            cost=1000,
            max_seats=None,
        )

        membership = OrganisationMembership.objects.create(
            organisation=org,
            membership_option=option,
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date() + relativedelta(years=1),
            approved_datetime=timezone.now(),
            created_datetime=timezone.now(),
            seats=10,
        )

        summary = membership.seats_summary()
        assert isinstance(summary, str)
        assert "Membership has limit" not in summary
        assert f"Occupied: {membership.occupied_seats} / {membership.seats}" in summary

    def test_occupied_seats_counted_only_when_active_or_pending(self):
        org = OrganisationFactory()
        option = MembershipOption.objects.create(
            name="Annual",
            type=MembershipOptionType.ORGANISATION,
            duration=relativedelta(years=1),
            cost=1000,
            max_seats=10,
        )

        # Create membership that is active
        membership = OrganisationMembership.objects.create(
            organisation=org,
            membership_option=option,
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date() + relativedelta(years=1),
            approved_datetime=timezone.now(),
            created_datetime=timezone.now(),
            seats=10,
        )

        # Create an organisation member who has accepted
        user = UserFactory()
        OrganisationMember.objects.create(
            user=user,
            organisation=org,
            created_datetime=timezone.now(),
            accepted_datetime=timezone.now(),
        )

        assert membership.occupied_seats == 1
        # Summary should include occupied count
        assert (
            f"Occupied: {membership.occupied_seats} / {membership.seats}"
            in membership.seats_summary()
        )
