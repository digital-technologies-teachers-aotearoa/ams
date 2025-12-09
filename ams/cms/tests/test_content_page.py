# ruff: noqa: S106

import datetime
from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client
from wagtail.models import Page

from ams.cms.models import ContentPage
from ams.cms.models import HomePage
from ams.memberships.models import IndividualMembership
from ams.memberships.models import MembershipOption
from ams.memberships.models import MembershipOptionType


@pytest.mark.django_db
class TestContentPageVisibility:
    def setup_method(self):
        # Ensure HomePage exists
        self.homepage = HomePage.objects.first()
        if not self.homepage:
            root = Page.get_first_root_node()
            self.homepage = HomePage(title="Home", slug="home")
            root.add_child(instance=self.homepage)
            self.homepage.save()

        self.client = Client()
        self.User = get_user_model()

    def create_content_page(self, visibility):
        page = ContentPage(
            title=f"{visibility.title()} Page",
            slug=f"{visibility}-page",
            visibility=visibility,
        )
        self.homepage.add_child(instance=page)
        page.save_revision().publish()
        return page

    def test_public_page_visible_to_anonymous(self):
        page = self.create_content_page(ContentPage.VISIBILITY_PUBLIC)
        response = self.client.get(page.url)
        assert response.status_code == HTTPStatus.OK

    def test_members_page_forbidden_to_anonymous(self):
        page = self.create_content_page(ContentPage.VISIBILITY_MEMBERS)
        response = self.client.get(page.url)
        assert response.status_code == HTTPStatus.FORBIDDEN
        assert b"only available to members" in response.content

    def test_members_page_visible_to_superuser(self):
        user = self.User.objects.create_superuser(
            username="admin",
            password="pw",
            email="admin@example.com",
        )
        self.client.force_login(user)
        page = self.create_content_page(ContentPage.VISIBILITY_MEMBERS)
        response = self.client.get(page.url)
        assert response.status_code == HTTPStatus.OK

    def test_members_page_forbidden_to_staff(self):
        user = self.User.objects.create_user(
            username="staff",
            password="pw",
            email="staff@example.com",
            is_staff=True,
        )
        self.client.force_login(user)
        page = self.create_content_page(ContentPage.VISIBILITY_MEMBERS)
        response = self.client.get(page.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_members_page_visible_to_member(self):
        user = self.User.objects.create_user(
            username="member",
            password="pw",
            email="member@example.com",
        )
        # Give user an active membership
        option = MembershipOption.objects.create(
            name="Test Option",
            type=MembershipOptionType.INDIVIDUAL,
            duration=datetime.timedelta(days=365),
            cost=0,
        )
        now = datetime.datetime.now(tz=datetime.UTC)
        IndividualMembership.objects.create(
            user=user,
            membership_option=option,
            start_date=(now - datetime.timedelta(days=1)).date(),
            expiry_date=(now + datetime.timedelta(days=10)).date(),
            created_datetime=now,
            approved_datetime=now,
        )
        self.client.force_login(user)
        page = self.create_content_page(ContentPage.VISIBILITY_MEMBERS)
        response = self.client.get(page.url)
        assert response.status_code == HTTPStatus.OK

    def test_members_page_forbidden_to_non_member(self):
        user = self.User.objects.create_user(
            username="nonmember",
            password="pw",
            email="nonmember@example.com",
        )
        self.client.force_login(user)
        page = self.create_content_page(ContentPage.VISIBILITY_MEMBERS)
        response = self.client.get(page.url)
        assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db
class TestContentPageSlugValidation:
    """Test reserved slug validation for ContentPage."""

    def test_reserved_slug_validation_for_homepage_child(self):
        """Test that reserved slugs are blocked for direct children of HomePage."""
        # Get or create the HomePage
        homepage = HomePage.objects.first()
        if not homepage:
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
        homepage = HomePage.objects.first()
        if not homepage:
            root = Page.get_first_root_node()
            homepage = HomePage(
                title="Home",
                slug="home",
            )
            root.add_child(instance=homepage)
            homepage.save()

        # Create an intermediate content page (use unique slug to avoid conflicts)
        intermediate_page = ContentPage(
            title="Intermediate Page For Test",
            slug="intermediate-for-nested-test",
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
        homepage = HomePage.objects.first()
        if not homepage:
            root = Page.get_first_root_node()
            homepage = HomePage(
                title="Home",
                slug="home",
            )
            root.add_child(instance=homepage)
            homepage.save()

        # Create a page with a non-reserved slug (use unique slug to avoid conflicts)
        content_page = ContentPage(
            title="Test Non Reserved Page",
            slug="test-non-reserved",  # This should be allowed
        )
        homepage.add_child(instance=content_page)

        # Validation should not raise an error
        try:
            content_page.clean()
        except ValidationError:
            pytest.fail(
                "ValidationError should not be raised for non-reserved slugs",
            )
