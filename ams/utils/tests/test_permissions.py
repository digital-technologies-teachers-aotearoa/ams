"""Tests for permission utility functions."""

from unittest.mock import patch

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache

from ams.memberships.tests.factories import IndividualMembershipFactory
from ams.users.tests.factories import UserFactory
from ams.utils.permissions import _check_user_membership_core
from ams.utils.permissions import user_has_active_membership
from ams.utils.permissions import user_has_active_membership_request_cached

pytestmark = pytest.mark.django_db


class TestUserHasActiveMembership:
    """Test the user_has_active_membership function."""

    def setup_method(self):
        """Clear cache before each test."""
        cache.clear()

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

    def test_caching_works(self):
        """Test that results are cached and subsequent calls use cache."""
        # Arrange
        user = UserFactory()
        IndividualMembershipFactory(user=user, active=True)
        cache_key = f"user_has_active_membership_{user.id}"

        # Act - First call should hit database and cache result
        with patch("ams.utils.permissions.cache") as mock_cache:
            mock_cache.get.return_value = None  # Cache miss
            result1 = user_has_active_membership(user)
            mock_cache.set.assert_called_once_with(cache_key, True, 300)  # noqa: FBT003

        # Act - Second call should use cache
        with patch("ams.utils.permissions.cache") as mock_cache:
            mock_cache.get.return_value = True  # Cache hit
            result2 = user_has_active_membership(user)
            mock_cache.set.assert_not_called()

        # Assert
        assert result1 is True
        assert result2 is True

    def test_cache_key_based_on_user_id(self):
        """Test that cache keys are based on user ID."""
        # Arrange
        user1 = UserFactory()
        user2 = UserFactory()
        IndividualMembershipFactory(user=user1, active=True)

        # Act
        result1 = user_has_active_membership(user1)
        result2 = user_has_active_membership(user2)

        # Assert - Different users should have different cache keys
        cache_key1 = f"user_has_active_membership_{user1.id}"
        cache_key2 = f"user_has_active_membership_{user2.id}"

        assert cache.get(cache_key1) is True
        assert cache.get(cache_key2) is False
        assert result1 is True
        assert result2 is False


class TestUserHasActiveMembershipRequestCached:
    """Test the request-cached version of the function."""

    def test_request_caching_works(self):
        """Test that results are cached on the user object for the request."""
        # Arrange
        user = UserFactory()
        IndividualMembershipFactory(user=user, active=True)

        # Act - First call should set cache on user object
        result1 = user_has_active_membership_request_cached(user)

        # Verify cache attribute is set
        assert hasattr(user, "_cached_has_active_membership")
        assert user._cached_has_active_membership is True  # noqa: SLF001

        # Act - Second call should use cached value
        with patch("ams.utils.permissions.any") as mock_any:
            result2 = user_has_active_membership_request_cached(user)
            # any() should not be called on second invocation
            mock_any.assert_not_called()

        # Assert
        assert result1 is True
        assert result2 is True

    def test_superuser_not_cached(self):
        """Test that superuser status is not cached (immediate return)."""
        # Arrange
        user = UserFactory(is_superuser=True)

        # Act
        result = user_has_active_membership_request_cached(user)

        # Assert
        assert result is True
        assert not hasattr(user, "_cached_has_active_membership")


class TestCheckUserMembershipCore:
    """Test the core membership checking function."""

    def test_core_function_with_active_membership(self):
        """Test core function returns True for users with active membership."""
        # Arrange
        user = UserFactory()
        IndividualMembershipFactory(user=user, active=True)

        # Act
        result = _check_user_membership_core(user)

        # Assert
        assert result is True

    def test_core_function_with_no_membership(self):
        """Test core function returns False for users without membership."""
        # Arrange
        user = UserFactory()

        # Act
        result = _check_user_membership_core(user)

        # Assert
        assert result is False

    def test_core_function_with_expired_membership(self):
        """Test core function returns False for users with expired membership."""
        # Arrange
        user = UserFactory()
        IndividualMembershipFactory(user=user, expired=True)

        # Act
        result = _check_user_membership_core(user)

        # Assert
        assert result is False
