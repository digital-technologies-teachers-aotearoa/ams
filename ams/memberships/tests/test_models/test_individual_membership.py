from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from ams.memberships.models import MembershipStatus
from ams.memberships.tests.factories import IndividualMembershipFactory

pytestmark = pytest.mark.django_db


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


class TestIndividualMembershipQuerySet:
    """Test IndividualMembershipQuerySet methods."""

    def test_active_filters_cancelled_memberships(self):
        """Test that cancelled memberships are excluded from active()."""
        user = IndividualMembershipFactory().user
        active_membership = IndividualMembershipFactory(
            user=user,
            active=True,
        )
        cancelled_membership = IndividualMembershipFactory(
            user=user,
            cancelled=True,
        )

        active_memberships = user.individual_memberships.active()

        assert active_membership in active_memberships
        assert cancelled_membership not in active_memberships

    def test_active_filters_expired_memberships(self):
        """Test that expired memberships are excluded from active()."""
        user = IndividualMembershipFactory().user
        active_membership = IndividualMembershipFactory(
            user=user,
            active=True,
        )
        expired_membership = IndividualMembershipFactory(
            user=user,
            expired=True,
        )

        active_memberships = user.individual_memberships.active()

        assert active_membership in active_memberships
        assert expired_membership not in active_memberships

    def test_active_excludes_memberships_expiring_today(self):
        """Test memberships expiring today are EXCLUDED (expire at midnight)."""
        user = IndividualMembershipFactory().user
        # Create membership expiring today (should be excluded with __gt)
        today_expiry = IndividualMembershipFactory(
            user=user,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate(),
            approved_datetime=timezone.now(),
        )

        active_memberships = user.individual_memberships.active()

        assert today_expiry not in active_memberships

    def test_active_filters_future_memberships(self):
        """Test that future memberships are excluded from active()."""
        user = IndividualMembershipFactory().user
        active_membership = IndividualMembershipFactory(
            user=user,
            active=True,
        )
        future_membership = IndividualMembershipFactory(
            user=user,
            future=True,
        )

        active_memberships = user.individual_memberships.active()

        assert active_membership in active_memberships
        assert future_membership not in active_memberships

    def test_active_includes_current_memberships(self):
        """Test that current valid memberships are included."""
        user = IndividualMembershipFactory().user
        # Create membership: start <= today < expiry
        current_membership = IndividualMembershipFactory(
            user=user,
            start_date=timezone.localdate() - timedelta(days=10),
            expiry_date=timezone.localdate() + timedelta(days=10),
            approved_datetime=timezone.now(),
        )

        active_memberships = user.individual_memberships.active()

        assert current_membership in active_memberships
