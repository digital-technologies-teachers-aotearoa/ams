from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from ams.memberships.models import MembershipOption
from ams.memberships.models import MembershipStatus
from ams.memberships.tests.factories import IndividualMembershipFactory
from ams.memberships.tests.factories import MembershipOptionFactory
from ams.memberships.tests.factories import OrganisationMembershipFactory
from ams.users.tests.factories import OrganisationMemberFactory

pytestmark = pytest.mark.django_db


class TestMembershipOption:
    def test_str(self):
        # Arrange
        option = MembershipOptionFactory(
            name="Gold",
            individual=True,
            duration={"months": 1},
            cost=49.99,
        )
        # Act
        result_str = str(option)
        # Assert
        assert "Gold" in result_str
        assert "Individual" in result_str
        assert "1 month" in result_str
        assert "$49.99" in result_str

    def test_max_seats_optional(self):
        # Arrange & Act
        option = MembershipOptionFactory(
            individual=True,
            max_seats=None,
        )
        # Assert
        assert option.max_seats is None

    def test_max_seats_with_value(self):
        # Arrange & Act
        option = MembershipOptionFactory(
            organisation=True,
            max_seats=20,
        )
        # Assert
        assert option.max_seats == 20  # noqa: PLR2004

    def test_archived_defaults_false(self):
        # Arrange & Act
        option = MembershipOptionFactory()
        # Assert
        assert option.archived is False

    def test_archived_can_be_set_true(self):
        # Arrange & Act
        option = MembershipOptionFactory(archived=True)
        # Assert
        assert option.archived is True

    def test_delete_with_no_memberships_succeeds(self):
        # Arrange
        option = MembershipOptionFactory()
        option_id = option.id
        # Act
        option.delete()
        # Assert

        assert not MembershipOption.objects.filter(id=option_id).exists()

    def test_delete_with_individual_memberships_raises(self):
        # Arrange
        option = MembershipOptionFactory(individual=True)
        IndividualMembershipFactory(membership_option=option)
        # Act & Assert
        with pytest.raises(ValidationError) as exc:
            option.delete()
        assert "Cannot delete membership option with existing memberships" in str(
            exc.value,
        )
        assert "Archive it instead" in str(exc.value)

    def test_delete_with_organisation_memberships_raises(self):
        # Arrange
        option = MembershipOptionFactory(organisation=True)
        OrganisationMembershipFactory(membership_option=option)
        # Act & Assert
        with pytest.raises(ValidationError) as exc:
            option.delete()
        assert "Cannot delete membership option with existing memberships" in str(
            exc.value,
        )
        assert "Archive it instead" in str(exc.value)


class TestIndividualMembership:
    def test_str(self):
        # Arrange
        membership = IndividualMembershipFactory()
        # Act
        result = str(membership)
        # Assert
        assert membership.user.get_full_name() in result
        assert membership.membership_option.name in result
        assert "Status:" in result

    def test_clean_expiry_before_start_raises(self):
        # Arrange
        membership = IndividualMembershipFactory()
        membership.start_date = timezone.localdate()
        membership.expiry_date = membership.start_date - timedelta(days=1)
        # Act & Assert
        with pytest.raises(ValidationError) as exc:
            membership.clean()
        assert "Expiry date must be after start date." in str(exc.value)

    def test_is_expired(self):
        # Arrange
        membership = IndividualMembershipFactory(expired=True)
        # Act
        result = membership.is_expired()
        # Assert
        assert result is True

    def test_is_expired_with_none_expiry_date(self):
        # Arrange
        membership = IndividualMembershipFactory()
        membership.expiry_date = None
        # Act
        result = membership.is_expired()
        # Assert - membership without expiry_date should not be considered expired
        assert result is False

    @pytest.mark.parametrize(
        ("approved", "cancelled", "start_offset", "expected_status"),
        [
            (None, None, 0, MembershipStatus.PENDING),
            (timezone.now(), None, 0, MembershipStatus.ACTIVE),
            (timezone.now(), timezone.now(), 0, MembershipStatus.CANCELLED),
            (None, None, -10, MembershipStatus.EXPIRED),
            (None, None, 10, MembershipStatus.PENDING),
        ],
    )
    def test_status(self, approved, cancelled, start_offset, expected_status):
        # Arrange
        start_date = timezone.localdate() + timedelta(days=start_offset)
        expiry_date = start_date + timedelta(days=1)
        membership = IndividualMembershipFactory(
            start_date=start_date,
            expiry_date=expiry_date,
            approved_datetime=approved,
            cancelled_datetime=cancelled,
        )
        # Act
        status = membership.status()
        # Assert
        assert status == expected_status


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
        membership = OrganisationMembershipFactory()
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
