"""Tests for CMS models and functionality."""

import pytest
from django.core.exceptions import ValidationError
from wagtail.models import Page

from ams.cms.models import ContentPage
from ams.cms.models import HomePage


@pytest.mark.django_db
class TestContentPageSlugValidation:
    """Test reserved slug validation for ContentPage."""

    def test_reserved_slug_validation_for_homepage_child(self):
        """Test that reserved slugs are blocked for direct children of HomePage."""
        # Get or create the HomePage
        try:
            homepage = HomePage.objects.get()
        except HomePage.DoesNotExist:
            # Create a root page if it doesn't exist
            root = Page.get_first_root_node()
            homepage = HomePage(
                title="Home",
                slug="home",
            )
            root.add_child(instance=homepage)
            homepage.save()

        # Try to create a page with a reserved slug as a child of HomePage
        content_page = ContentPage(
            title="Forum Page",
            slug="forum",  # This should be blocked
        )

        # Validation should raise an error during add_child (calls save/full_clean)
        with pytest.raises(ValidationError) as exc_info:
            homepage.add_child(instance=content_page)

        assert "slug" in exc_info.value.message_dict
        assert "reserved for application URLs" in exc_info.value.message_dict["slug"][0]

    def test_reserved_slug_allowed_for_nested_page(self):
        """Test that reserved slugs are allowed for non-direct children of HomePage."""
        # Get or create the HomePage
        try:
            homepage = HomePage.objects.get()
        except HomePage.DoesNotExist:
            root = Page.get_first_root_node()
            homepage = HomePage(
                title="Home",
                slug="home",
            )
            root.add_child(instance=homepage)
            homepage.save()

        # Create an intermediate content page
        intermediate_page = ContentPage(
            title="Intermediate Page",
            slug="intermediate",
        )
        homepage.add_child(instance=intermediate_page)
        intermediate_page.save()

        # Create a nested page with reserved slug (should be allowed)
        nested_page = ContentPage(
            title="Forum Page",
            slug="forum",  # This should be allowed since it's not a direct child
        )
        intermediate_page.add_child(instance=nested_page)

        # Validation should not raise an error
        try:
            nested_page.clean()
        except ValidationError:
            pytest.fail(
                "ValidationError should not be raised for nested pages "
                "with reserved slugs",
            )

    def test_non_reserved_slug_allowed(self):
        """Test that non-reserved slugs are allowed for direct children of HomePage."""
        # Get or create the HomePage
        try:
            homepage = HomePage.objects.get()
        except HomePage.DoesNotExist:
            root = Page.get_first_root_node()
            homepage = HomePage(
                title="Home",
                slug="home",
            )
            root.add_child(instance=homepage)
            homepage.save()

        # Create a page with a non-reserved slug
        content_page = ContentPage(
            title="About Page",
            slug="about",  # This should be allowed
        )
        homepage.add_child(instance=content_page)

        # Validation should not raise an error
        try:
            content_page.clean()
        except ValidationError:
            pytest.fail(
                "ValidationError should not be raised for non-reserved slugs",
            )
