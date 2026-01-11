"""Tests for terms helper functions."""

from datetime import timedelta
from unittest.mock import Mock

import pytest
from django.core.cache import cache
from django.utils import timezone

from ams.terms.helpers import get_latest_term_versions
from ams.terms.helpers import get_pending_term_versions_for_user
from ams.terms.helpers import invalidate_pending_terms_cache
from ams.terms.tests.factories import TermAcceptanceFactory
from ams.terms.tests.factories import TermFactory
from ams.terms.tests.factories import TermVersionFactory
from ams.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestGetPendingTermVersionsForUser:
    """Tests for get_pending_term_versions_for_user helper."""

    def setup_method(self):
        """Clear cache before each test."""
        cache.clear()

    def test_returns_empty_for_anonymous_users(self):
        """Test that anonymous users get empty list."""
        anonymous_user = Mock(is_authenticated=False)
        result = get_pending_term_versions_for_user(anonymous_user)
        assert result == []

    def test_returns_current_active_unaccepted_versions(self):
        """Test returns only current, active, unaccepted versions."""
        user = UserFactory()
        term = TermFactory()

        # Create a current, active version
        current_version = TermVersionFactory(
            term=term,
            version="1.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        result = get_pending_term_versions_for_user(user)
        assert len(result) == 1
        assert result[0] == current_version

    def test_excludes_inactive_versions(self):
        """Test that inactive versions are not returned."""
        user = UserFactory()
        TermVersionFactory(
            is_active=False,
            date_active=timezone.now() - timedelta(days=1),
        )

        result = get_pending_term_versions_for_user(user)
        assert len(result) == 0

    def test_excludes_future_dated_versions(self):
        """Test that future-dated versions are not returned."""
        user = UserFactory()
        TermVersionFactory(
            is_active=True,
            date_active=timezone.now() + timedelta(days=1),
        )

        result = get_pending_term_versions_for_user(user)
        assert len(result) == 0

    def test_excludes_already_accepted_versions(self):
        """Test that already-accepted versions are not returned."""
        user = UserFactory()
        term_version = TermVersionFactory(
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        # User has already accepted this version
        TermAcceptanceFactory(user=user, term_version=term_version)

        result = get_pending_term_versions_for_user(user)
        assert len(result) == 0

    def test_deterministic_ordering_by_term_key(self):
        """Test results are ordered deterministically by term.key."""
        user = UserFactory()

        # Create terms with keys that would sort in specific order
        term_a = TermFactory(key="a-policy")
        term_z = TermFactory(key="z-policy")

        # Create one version per term
        version_a = TermVersionFactory(
            term=term_a,
            version="1.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )
        version_z = TermVersionFactory(
            term=term_z,
            version="1.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        result = get_pending_term_versions_for_user(user)

        # Should be ordered: a-policy, z-policy
        expected_terms = 2
        assert len(result) == expected_terms
        assert result[0] == version_a
        assert result[1] == version_z

    def test_returns_only_latest_version_of_each_term(self):
        """Test that only the latest version of each term is returned."""
        user = UserFactory()

        term = TermFactory(key="privacy-policy")

        # Create multiple versions with different activation dates
        TermVersionFactory(
            term=term,
            version="1.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=10),
        )
        latest_version = TermVersionFactory(
            term=term,
            version="2.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        result = get_pending_term_versions_for_user(user)

        # Should only return the latest version (2.0)
        assert len(result) == 1
        assert result[0] == latest_version
        assert result[0].version == "2.0"

    def test_latest_version_determined_by_date_active_not_version_number(self):
        """Test that latest version is determined by date_active, not version number."""
        user = UserFactory()

        term = TermFactory(key="terms-of-service")

        # Create versions where version number doesn't match date order
        # Version "2.0" activated first
        TermVersionFactory(
            term=term,
            version="2.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=10),
        )
        # Version "1.5" activated more recently (this should be "latest")
        version_1_5 = TermVersionFactory(
            term=term,
            version="1.5",
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        result = get_pending_term_versions_for_user(user)

        # Should return version 1.5 as it has more recent date_active
        assert len(result) == 1
        assert result[0] == version_1_5
        assert result[0].version == "1.5"

    def test_user_who_accepted_old_version_sees_new_version(self):
        """Test that user who accepted old version still sees newer version."""
        user = UserFactory()

        term = TermFactory(key="privacy-policy")

        # Old version
        old_version = TermVersionFactory(
            term=term,
            version="1.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=10),
        )

        # User accepted old version
        TermAcceptanceFactory(user=user, term_version=old_version)

        # New version activated
        new_version = TermVersionFactory(
            term=term,
            version="2.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        result = get_pending_term_versions_for_user(user)

        # User should see the new version
        assert len(result) == 1
        assert result[0] == new_version

    def test_user_who_accepted_latest_version_sees_nothing(self):
        """Test that user who accepted latest version sees no pending terms."""
        user = UserFactory()

        term = TermFactory(key="privacy-policy")

        # Old version
        TermVersionFactory(
            term=term,
            version="1.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=10),
        )

        # Latest version
        latest_version = TermVersionFactory(
            term=term,
            version="2.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        # User accepted latest version
        TermAcceptanceFactory(user=user, term_version=latest_version)

        result = get_pending_term_versions_for_user(user)

        # User should see nothing
        assert len(result) == 0

    def test_multiple_terms_each_with_multiple_versions(self):
        """Test correct behavior with multiple terms, each having multiple versions."""
        user = UserFactory()

        # Term A with 2 versions
        term_a = TermFactory(key="a-policy")
        TermVersionFactory(
            term=term_a,
            version="1.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=10),
        )
        version_a2 = TermVersionFactory(
            term=term_a,
            version="2.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=5),
        )

        # Term B with 3 versions
        term_b = TermFactory(key="b-policy")
        TermVersionFactory(
            term=term_b,
            version="1.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=15),
        )
        TermVersionFactory(
            term=term_b,
            version="2.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=10),
        )
        version_b3 = TermVersionFactory(
            term=term_b,
            version="3.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=2),
        )

        result = get_pending_term_versions_for_user(user)

        # Should only see latest version of each term
        expected_terms = 2
        assert len(result) == expected_terms
        assert result[0] == version_a2  # Latest for term A
        assert result[1] == version_b3  # Latest for term B

    def test_caching_behavior(self):
        """Test that results are cached for 5 minutes."""
        user = UserFactory()
        TermVersionFactory(
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        # First call - should query database
        result1 = get_pending_term_versions_for_user(user)

        # Create another version (should not appear due to caching)
        TermVersionFactory(
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        # Second call - should use cache
        result2 = get_pending_term_versions_for_user(user)

        assert len(result1) == 1
        assert len(result2) == 1  # Still 1 due to cache

    def test_cache_invalidation(self):
        """Test that cache can be invalidated."""
        user = UserFactory()
        TermVersionFactory(
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        # First call - cache result
        result1 = get_pending_term_versions_for_user(user)
        assert len(result1) == 1

        # Invalidate cache
        invalidate_pending_terms_cache(user)

        # Create another version
        TermVersionFactory(
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        # Second call - should see new version
        result2 = get_pending_term_versions_for_user(user)
        expected_terms = 2
        assert len(result2) == expected_terms

    def test_returns_only_current_versions_not_all_active(self):
        """Test that only current versions are returned
        (active + date_active <= now)."""
        user = UserFactory()

        # Create version that is active but not yet current
        TermVersionFactory(
            is_active=True,
            date_active=timezone.now() + timedelta(hours=1),
        )

        result = get_pending_term_versions_for_user(user)
        assert len(result) == 0


class TestGetLatestTermVersions:
    """Tests for get_latest_term_versions helper."""

    def setup_method(self):
        """Clear cache before each test."""
        cache.clear()

    def test_returns_empty_when_no_terms(self):
        """Test that empty list is returned when no terms exist."""
        result = get_latest_term_versions()
        assert result == []

    def test_returns_latest_version_of_each_term(self):
        """Test returns only the latest version of each term."""
        term = TermFactory(key="privacy-policy")

        # Create multiple versions with different activation dates
        TermVersionFactory(
            term=term,
            version="1.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=10),
        )
        latest_version = TermVersionFactory(
            term=term,
            version="2.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        result = get_latest_term_versions()

        # Should only return the latest version (2.0)
        assert len(result) == 1
        assert result[0] == latest_version
        assert result[0].version == "2.0"

    def test_excludes_inactive_versions(self):
        """Test that inactive versions are not returned."""
        TermVersionFactory(
            is_active=False,
            date_active=timezone.now() - timedelta(days=1),
        )

        result = get_latest_term_versions()
        assert len(result) == 0

    def test_excludes_future_dated_versions(self):
        """Test that future-dated versions are not returned."""
        TermVersionFactory(
            is_active=True,
            date_active=timezone.now() + timedelta(days=1),
        )

        result = get_latest_term_versions()
        assert len(result) == 0

    def test_deterministic_ordering_by_term_key(self):
        """Test results are ordered deterministically by term.key."""
        # Create terms with keys that would sort in specific order
        term_a = TermFactory(key="a-policy")
        term_z = TermFactory(key="z-policy")

        # Create one version per term
        version_a = TermVersionFactory(
            term=term_a,
            version="1.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )
        version_z = TermVersionFactory(
            term=term_z,
            version="1.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        result = get_latest_term_versions()

        # Should be ordered: a-policy, z-policy
        expected_terms = 2
        assert len(result) == expected_terms
        assert result[0] == version_a
        assert result[1] == version_z

    def test_latest_determined_by_date_active_not_version_number(self):
        """Test that latest version is determined by date_active, not version number."""
        term = TermFactory(key="terms-of-service")

        # Create versions where version number doesn't match date order
        # Version "2.0" activated first
        TermVersionFactory(
            term=term,
            version="2.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=10),
        )
        # Version "1.5" activated more recently (this should be "latest")
        version_1_5 = TermVersionFactory(
            term=term,
            version="1.5",
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        result = get_latest_term_versions()

        # Should return version 1.5 as it has more recent date_active
        assert len(result) == 1
        assert result[0] == version_1_5
        assert result[0].version == "1.5"

    def test_multiple_terms_each_with_multiple_versions(self):
        """Test correct behavior with multiple terms, each having multiple versions."""
        # Term A with 2 versions
        term_a = TermFactory(key="a-policy")
        TermVersionFactory(
            term=term_a,
            version="1.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=10),
        )
        version_a2 = TermVersionFactory(
            term=term_a,
            version="2.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=5),
        )

        # Term B with 3 versions
        term_b = TermFactory(key="b-policy")
        TermVersionFactory(
            term=term_b,
            version="1.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=15),
        )
        TermVersionFactory(
            term=term_b,
            version="2.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=10),
        )
        version_b3 = TermVersionFactory(
            term=term_b,
            version="3.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=2),
        )

        result = get_latest_term_versions()

        # Should only see latest version of each term
        expected_terms = 2
        assert len(result) == expected_terms
        assert result[0] == version_a2  # Latest for term A
        assert result[1] == version_b3  # Latest for term B
