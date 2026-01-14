"""Tests for breadcrumb functionality."""

import uuid
from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import reverse
from wagtail.models import Page

from ams.cms.models import HomePage
from ams.organisations.tests.factories import OrganisationFactory
from ams.users.tests.factories import UserFactory
from ams.utils.breadcrumbs import BREADCRUMB_REGISTRY
from ams.utils.breadcrumbs import _get_cached_value
from ams.utils.breadcrumbs import _get_kwargs_for_view
from ams.utils.breadcrumbs import _get_organisation_name
from ams.utils.breadcrumbs import _get_user_dashboard_label
from ams.utils.breadcrumbs import get_breadcrumbs_for_django_page
from ams.utils.breadcrumbs import get_current_view_name
from ams.utils.breadcrumbs import is_homepage

User = get_user_model()


class TestGetCachedValue:
    """Tests for _get_cached_value function."""

    def test_caches_value_on_request(self):
        """Test that value is cached on the request object."""
        request = RequestFactory().get("/")

        # First call
        result1 = _get_cached_value(request, "test_key", lambda: "test_value")
        assert result1 == "test_value"

        # Verify cache exists
        assert hasattr(request, "breadcrumb_cache")
        assert "test_key" in request.breadcrumb_cache
        assert request.breadcrumb_cache["test_key"] == "test_value"

    def test_uses_cached_value_on_subsequent_calls(self):
        """Test that subsequent calls use the cached value."""
        request = RequestFactory().get("/")
        call_count = 0

        def getter():
            nonlocal call_count
            call_count += 1
            return f"value_{call_count}"

        # First call
        result1 = _get_cached_value(request, "test_key", getter)
        assert result1 == "value_1"
        assert call_count == 1

        # Second call should use cached value
        result2 = _get_cached_value(request, "test_key", getter)
        assert result2 == "value_1"
        assert call_count == 1  # Should not have called getter again

    def test_different_keys_have_separate_cache(self):
        """Test that different cache keys store different values."""
        request = RequestFactory().get("/")

        result1 = _get_cached_value(request, "key1", lambda: "value1")
        result2 = _get_cached_value(request, "key2", lambda: "value2")

        assert result1 == "value1"
        assert result2 == "value2"
        assert request.breadcrumb_cache["key1"] == "value1"
        assert request.breadcrumb_cache["key2"] == "value2"


class TestGetOrganisationName:
    """Tests for _get_organisation_name function."""

    def test_returns_organisation_name_when_exists(self, db):
        """Test that it returns the organisation name when it exists."""
        org = OrganisationFactory(name="Test Organisation")
        request = RequestFactory().get("/")

        result = _get_organisation_name(request, uuid=org.uuid)

        assert result == "Test Organisation"

    def test_returns_default_label_when_org_not_found(self, db):
        """Test that it returns default label when organisation doesn't exist."""
        request = RequestFactory().get("/")

        result = _get_organisation_name(request, uuid=uuid.uuid4())

        assert result == "Organisation"

    def test_returns_default_label_when_no_uuid_provided(self):
        """Test that it returns default label when no UUID is provided."""
        request = RequestFactory().get("/")

        result = _get_organisation_name(request)

        assert result == "Organisation"

    def test_caches_organisation_name(self, db):
        """Test that organisation name is cached."""
        org = OrganisationFactory(name="Test Organisation")
        request = RequestFactory().get("/")

        # First call
        result1 = _get_organisation_name(request, uuid=org.uuid)
        assert result1 == "Test Organisation"

        # Verify it's cached
        assert hasattr(request, "breadcrumb_cache")
        assert "org_name" in request.breadcrumb_cache


class TestGetUserDashboardLabel:
    """Tests for _get_user_dashboard_label function."""

    def test_returns_user_full_name(self, db):
        """Test that it returns the user's full name."""
        user = UserFactory(first_name="John", last_name="Doe")
        request = RequestFactory().get("/")

        result = _get_user_dashboard_label(request, username=user.username)

        assert result == "John Doe"

    def test_returns_default_label_when_no_username(self):
        """Test that it returns default label when no username provided."""
        request = RequestFactory().get("/")

        result = _get_user_dashboard_label(request)

        assert result == "User"

    def test_caches_user_name(self, db):
        """Test that user name is cached."""
        user = UserFactory(first_name="John", last_name="Doe")
        request = RequestFactory().get("/")

        # First call
        result = _get_user_dashboard_label(request, username=user.username)
        assert result == "John Doe"

        # Verify it's cached
        assert hasattr(request, "breadcrumb_cache")
        assert "user_name" in request.breadcrumb_cache


class TestGetCurrentViewName:
    """Tests for get_current_view_name function."""

    def test_returns_view_name_with_namespace(self, db):
        """Test that it returns view name with namespace."""
        user = UserFactory()
        url = reverse("users:detail", kwargs={"username": user.username})
        request = RequestFactory().get(url)

        # Manually set path_info to match the URL
        request.path_info = url

        result = get_current_view_name(request)

        assert result == "users:detail"

    def test_returns_none_for_invalid_path(self):
        """Test that it returns None for non-existent paths."""
        request = RequestFactory().get("/non/existent/path/")
        request.path_info = "/non/existent/path/"

        result = get_current_view_name(request)

        assert result is None

    def test_returns_view_name_without_namespace(self):
        """Test that it returns view name for views without namespace."""
        url = reverse("root_redirect")
        request = RequestFactory().get(url)
        request.path_info = url

        result = get_current_view_name(request)

        assert result == "root_redirect"


class TestIsHomepage:
    """Tests for is_homepage function."""

    def test_returns_true_for_wagtail_homepage(self):
        """Test that it returns True for Wagtail HomePage instances."""
        request = RequestFactory().get("/")
        # Mock a Wagtail page attribute - use a mock object to avoid DB
        mock_page = Mock(spec=HomePage)
        request.page = mock_page

        result = is_homepage(request)

        assert result is True

    def test_returns_false_for_non_homepage_wagtail_page(self):
        """Test that it returns False for non-HomePage Wagtail pages."""
        request = RequestFactory().get("/")
        # Use a mock object to avoid DB
        mock_page = Mock(spec=Page)
        request.page = mock_page

        result = is_homepage(request)

        assert result is False

    def test_returns_true_for_root_redirect_view(self):
        """Test that it returns True for root_redirect view."""
        url = reverse("root_redirect")
        request = RequestFactory().get(url)
        request.path_info = url

        result = is_homepage(request)

        assert result is True

    def test_returns_true_for_root_path(self):
        """Test that it returns True for root path."""
        request = RequestFactory().get("/")
        request.path_info = "/"

        result = is_homepage(request)

        assert result is True

    def test_returns_true_for_language_prefixed_root(self):
        """Test that it returns True for language-prefixed root paths."""
        for lang_path in ["/en", "/de", "/es", "/fr"]:
            request = RequestFactory().get(lang_path)
            request.path_info = lang_path

            result = is_homepage(request)

            assert result is True, f"Failed for path: {lang_path}"

    def test_returns_false_for_non_homepage_path(self):
        """Test that it returns False for non-homepage paths."""
        request = RequestFactory().get("/some/other/path/")
        request.path_info = "/some/other/path/"

        result = is_homepage(request)

        assert result is False


class TestGetKwargsForView:
    """Tests for _get_kwargs_for_view function."""

    def test_adds_username_for_users_detail_when_authenticated(self, db):
        """Test that it adds username for users:detail when user is authenticated."""
        user = UserFactory()
        request = RequestFactory().get("/")
        request.user = user

        result = _get_kwargs_for_view(request, "users:detail", {})

        assert result == {"username": user.username}

    def test_preserves_existing_kwargs(self, db):
        """Test that it preserves existing kwargs."""
        user = UserFactory()
        request = RequestFactory().get("/")
        request.user = user

        existing_kwargs = {"some": "value"}
        result = _get_kwargs_for_view(request, "users:detail", existing_kwargs)

        assert result == {"some": "value", "username": user.username}

    def test_does_not_override_username_if_already_present(self, db):
        """Test that it doesn't override username if already present."""
        user = UserFactory()
        request = RequestFactory().get("/")
        request.user = user

        existing_kwargs = {"username": "other_user"}
        result = _get_kwargs_for_view(request, "users:detail", existing_kwargs)

        assert result == {"username": "other_user"}

    def test_returns_unchanged_for_other_views(self, db):
        """Test that it returns unchanged kwargs for other views."""
        user = UserFactory()
        request = RequestFactory().get("/")
        request.user = user

        kwargs = {"uuid": "some-uuid"}
        result = _get_kwargs_for_view(request, "organisations:detail", kwargs)

        assert result == kwargs


class TestGetBreadcrumbsForDjangoPage:
    """Tests for get_breadcrumbs_for_django_page function."""

    def test_generates_simple_breadcrumbs(self, db):
        """Test that it generates breadcrumbs for a simple page."""
        user = UserFactory(first_name="John", last_name="Doe")
        request = RequestFactory().get("/")
        request.user = user

        result = get_breadcrumbs_for_django_page(
            request,
            "users:update",
            username=user.username,
        )

        # Should have: Home -> User Dashboard -> Update Account
        expected_breadcrumbs = 3
        assert len(result) == expected_breadcrumbs

        # Check home breadcrumb
        assert result[0]["title"] == "Home"
        assert result[0]["is_active"] is False
        assert result[0]["url"] == reverse("root_redirect")

        # Check user dashboard breadcrumb
        assert result[1]["title"] == "John Doe"
        assert result[1]["is_active"] is False
        assert result[1]["url"] == reverse(
            "users:detail",
            kwargs={"username": user.username},
        )

        # Check update account breadcrumb
        assert result[2]["title"] == "Update Account"
        assert result[2]["is_active"] is True

    def test_generates_nested_breadcrumbs(self, db):
        """Test that it generates breadcrumbs for nested pages."""
        user = UserFactory(first_name="Jane", last_name="Smith")
        org = OrganisationFactory(name="ACME Corp")
        request = RequestFactory().get("/")
        request.user = user

        result = get_breadcrumbs_for_django_page(
            request,
            "organisations:update",
            username=user.username,
            uuid=org.uuid,
        )

        # Should have: Home -> User Dashboard -> Organisation -> Edit Organisation
        expected_breadcrumbs = 4
        assert len(result) == expected_breadcrumbs

        # Check home
        assert result[0]["title"] == "Home"

        # Check user dashboard
        assert result[1]["title"] == "Jane Smith"

        # Check organisation
        assert result[2]["title"] == "ACME Corp"
        assert result[2]["is_active"] is False

        # Check edit organisation
        assert result[3]["title"] == "Edit Organisation"
        assert result[3]["is_active"] is True

    def test_handles_view_not_in_registry(self, db):
        """Test that it handles views not in the registry."""
        user = UserFactory()
        request = RequestFactory().get("/")
        request.user = user

        result = get_breadcrumbs_for_django_page(
            request,
            "unknown:view",
            username=user.username,
        )

        # Should only have home
        assert len(result) == 1
        assert result[0]["title"] == "Home"

    def test_prevents_circular_references(self, db):
        """Test that it prevents circular references in breadcrumb chains."""
        # Temporarily add a circular reference
        original_parent = BREADCRUMB_REGISTRY.get("users:detail", {}).get("parent")
        BREADCRUMB_REGISTRY["users:detail"]["parent"] = "users:detail"

        user = UserFactory()
        request = RequestFactory().get("/")
        request.user = user

        try:
            result = get_breadcrumbs_for_django_page(
                request,
                "users:detail",
                username=user.username,
            )

            # Should only have home and the view itself (circular ref prevented)
            expected_breadcrumbs = 2
            assert len(result) == expected_breadcrumbs
            assert result[0]["title"] == "Home"
        finally:
            # Restore original configuration
            if original_parent is None:
                BREADCRUMB_REGISTRY["users:detail"]["parent"] = None
            else:
                BREADCRUMB_REGISTRY["users:detail"]["parent"] = original_parent

    def test_handles_reverse_match_errors(self, db):
        """Test that it handles NoReverseMatch errors gracefully."""
        user = UserFactory()
        request = RequestFactory().get("/")
        request.user = user

        # Try to generate breadcrumbs without required kwargs
        result = get_breadcrumbs_for_django_page(
            request,
            "organisations:update",  # Missing uuid kwarg
        )

        # Should still generate breadcrumbs, but with None URL for failed reverse
        assert len(result) >= 1
        # Check that at least home is there
        assert result[0]["title"] == "Home"

    def test_top_level_page_without_parent(self, db):
        """Test that top-level pages without parent work correctly."""
        request = RequestFactory().get("/")

        result = get_breadcrumbs_for_django_page(request, "account_login")

        # Should have: Home -> Sign In
        expected_breadcrumbs = 2
        assert len(result) == expected_breadcrumbs
        assert result[0]["title"] == "Home"
        assert result[1]["title"] == "Sign In"
        assert result[1]["is_active"] is True

    def test_caching_works_across_breadcrumb_generation(self, db):
        """Test that caching works properly during breadcrumb generation."""
        user = UserFactory(first_name="John", last_name="Doe")
        org = OrganisationFactory(name="Test Org")
        request = RequestFactory().get("/")
        request.user = user

        # Generate breadcrumbs that should trigger caching
        get_breadcrumbs_for_django_page(
            request,
            "organisations:update",
            username=user.username,
            uuid=org.uuid,
        )

        # Verify cache was populated
        assert hasattr(request, "breadcrumb_cache")
        assert "user_name" in request.breadcrumb_cache
        assert "org_name" in request.breadcrumb_cache

        # Verify cached values are correct
        assert request.breadcrumb_cache["user_name"] == "John Doe"
        assert request.breadcrumb_cache["org_name"] == "Test Org"

    def test_membership_apply_individual_breadcrumbs(self, db):
        """Test breadcrumbs for individual membership application."""
        user = UserFactory(first_name="Alice", last_name="Wonder")
        request = RequestFactory().get("/")
        request.user = user

        result = get_breadcrumbs_for_django_page(
            request,
            "memberships:apply-individual",
            username=user.username,
        )

        # Should have: Home -> User Dashboard -> Apply for Membership
        expected_breadcrumbs = 3
        assert len(result) == expected_breadcrumbs
        assert result[0]["title"] == "Home"
        assert result[1]["title"] == "Alice Wonder"
        assert result[2]["title"] == "Apply for Membership"
        assert result[2]["is_active"] is True

    def test_organisation_invite_member_breadcrumbs(self, db):
        """Test breadcrumbs for organisation member invitation."""
        user = UserFactory(first_name="Bob", last_name="Builder")
        org = OrganisationFactory(name="Builders Inc")
        request = RequestFactory().get("/")
        request.user = user

        result = get_breadcrumbs_for_django_page(
            request,
            "organisations:invite_member",
            username=user.username,
            uuid=org.uuid,
        )

        # Should have: Home -> User Dashboard -> Organisation -> Invite Member
        expected_breadcrumbs = 4
        assert len(result) == expected_breadcrumbs
        assert result[0]["title"] == "Home"
        assert result[1]["title"] == "Bob Builder"
        assert result[2]["title"] == "Builders Inc"
        assert result[3]["title"] == "Invite Member"
        assert result[3]["is_active"] is True


class TestBreadcrumbRegistry:
    """Tests for BREADCRUMB_REGISTRY configuration."""

    def test_registry_has_expected_entries(self):
        """Test that registry contains expected entries."""
        expected_keys = [
            "users:detail",
            "users:update",
            "memberships:apply-individual",
            "organisations:create",
            "organisations:detail",
            "organisations:update",
            "account_login",
            "account_signup",
        ]

        for key in expected_keys:
            assert key in BREADCRUMB_REGISTRY, f"Missing key: {key}"

    def test_all_entries_have_required_fields(self):
        """Test that all registry entries have either label or label_getter."""
        for view_name, config in BREADCRUMB_REGISTRY.items():
            # Each entry must have parent (can be None)
            assert "parent" in config, f"{view_name} missing 'parent'"

            # Each entry must have either label or label_getter
            has_label = "label" in config
            has_getter = "label_getter" in config
            assert has_label or has_getter, (
                f"{view_name} must have 'label' or 'label_getter'"
            )

    def test_parent_references_are_valid(self):
        """Test that parent references point to valid entries or None."""
        for view_name, config in BREADCRUMB_REGISTRY.items():
            parent = config.get("parent")
            if parent is not None:
                assert parent in BREADCRUMB_REGISTRY, (
                    f"{view_name} has invalid parent: {parent}"
                )
