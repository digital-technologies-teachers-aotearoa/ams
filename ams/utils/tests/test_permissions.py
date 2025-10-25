"""Tests for permission utility functions."""

import pytest
from django.contrib.auth.models import AnonymousUser

from ams.memberships.tests.factories import IndividualMembershipFactory
from ams.users.tests.factories import UserFactory
from ams.utils.permissions import user_has_active_membership

pytestmark = pytest.mark.django_db


class TestUserHasActiveMembership:
    """Test the user_has_active_membership function."""

    def test_unauthenticated_user_has_no_access(self):
        """Unauthenticated users should not have access."""
        # Arrange
        user = AnonymousUser()

        # Act
        result = user_has_active_membership(user)

        # Assert
        assert result is False

    def test_superuser_has_access(self):
        """Superusers should always have access."""
        # Arrange
        user = UserFactory(is_superuser=True)

        # Act
        result = user_has_active_membership(user)

        # Assert
        assert result is True

    def test_user_with_active_membership_has_access(self):
        """Users with active memberships should have access."""
        # Arrange
        user = UserFactory()
        IndividualMembershipFactory(user=user, active=True)

        # Act
        result = user_has_active_membership(user)

        # Assert
        assert result is True

    def test_user_with_pending_membership_has_no_access(self):
        """Users with pending memberships should not have access."""
        # Arrange
        user = UserFactory()
        IndividualMembershipFactory(user=user, pending=True)

        # Act
        result = user_has_active_membership(user)

        # Assert
        assert result is False

    def test_user_with_cancelled_membership_has_no_access(self):
        """Users with cancelled memberships should not have access."""
        # Arrange
        user = UserFactory()
        IndividualMembershipFactory(user=user, cancelled=True)

        # Act
        result = user_has_active_membership(user)

        # Assert
        assert result is False

    def test_user_with_expired_membership_has_no_access(self):
        """Users with expired memberships should not have access."""
        # Arrange
        user = UserFactory()
        IndividualMembershipFactory(user=user, expired=True)

        # Act
        result = user_has_active_membership(user)

        # Assert
        assert result is False

    def test_user_with_no_memberships_has_no_access(self):
        """Users with no memberships should not have access."""
        # Arrange
        user = UserFactory()

        # Act
        result = user_has_active_membership(user)

        # Assert
        assert result is False

    def test_user_with_multiple_memberships_one_active(self):
        """Users with at least one active membership should have access."""
        # Arrange
        user = UserFactory()
        IndividualMembershipFactory(user=user, expired=True)
        IndividualMembershipFactory(user=user, active=True)
        IndividualMembershipFactory(user=user, pending=True)

        # Act
        result = user_has_active_membership(user)

        # Assert
        assert result is True

    def test_user_with_multiple_memberships_multiple_active(self):
        """Users with at least one active membership should have access."""
        # Arrange
        user = UserFactory()
        IndividualMembershipFactory(user=user, active=True)
        IndividualMembershipFactory(user=user, active=True)
        IndividualMembershipFactory(user=user, active=True)

        # Act
        result = user_has_active_membership(user)

        # Assert
        assert result is True
