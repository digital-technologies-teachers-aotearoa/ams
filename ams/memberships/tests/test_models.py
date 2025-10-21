from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from ams.memberships.models import MembershipStatus

from .factories import IndividualMembershipFactory
from .factories import MembershipOptionFactory
from .factories import OrganisationMembershipFactory

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

    def test_expires_in_days(self):
        # Arrange
        days_ahead = 5
        membership = IndividualMembershipFactory(
            expiry_date=timezone.localdate() + timedelta(days=days_ahead),
        )
        # Act
        days = membership.expires_in_days()
        # Assert
        assert days == days_ahead

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

    def test_expires_in_days(self):
        # Arrange
        days_ahead = 3
        membership = OrganisationMembershipFactory(
            expiry_date=timezone.localdate() + timedelta(days=days_ahead),
        )
        # Act
        days = membership.expires_in_days()
        # Assert
        assert days == days_ahead

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
