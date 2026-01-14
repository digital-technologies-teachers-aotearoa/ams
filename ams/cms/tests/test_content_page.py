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


@pytest.mark.django_db
class TestContentPageStructureOnly:
    """Test is_structure_only functionality for ContentPage."""

    def setup_method(self):
        """Set up test data."""
        # Ensure HomePage exists
        self.homepage = HomePage.objects.first()
        if not self.homepage:
            root = Page.get_first_root_node()
            self.homepage = HomePage(title="Home", slug="home")
            root.add_child(instance=self.homepage)
            self.homepage.save()

        self.client = Client()

    def test_structure_only_redirects_to_first_child(self):
        """Test that a structure-only page redirects to its first live child."""
        # Create structure-only parent page
        parent = ContentPage(
            title="Parent Page",
            slug="parent",
            is_structure_only=True,
        )
        self.homepage.add_child(instance=parent)
        parent.save_revision().publish()

        # Create first child page
        child1 = ContentPage(
            title="Child 1",
            slug="child-1",
        )
        parent.add_child(instance=child1)
        child1.save_revision().publish()

        # Create second child page
        child2 = ContentPage(
            title="Child 2",
            slug="child-2",
        )
        parent.add_child(instance=child2)
        child2.save_revision().publish()

        # Request the parent page - should redirect to first child
        response = self.client.get(parent.url)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == child1.url

    def test_structure_only_without_children_returns_404(self):
        """Test that a structure-only page without children returns 404."""
        # Create structure-only page with no children
        page = ContentPage(
            title="Empty Structure Page",
            slug="empty-structure",
            is_structure_only=True,
        )
        self.homepage.add_child(instance=page)
        page.save_revision().publish()

        # Request the page - should return 404
        response = self.client.get(page.url)
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_structure_only_skips_unpublished_children(self):
        """Test that structure-only page skips draft children and finds first live
        one."""
        # Create structure-only parent page
        parent = ContentPage(
            title="Parent Page",
            slug="parent-skip-draft",
            is_structure_only=True,
        )
        self.homepage.add_child(instance=parent)
        parent.save_revision().publish()

        # Create draft child (not published)
        draft_child = ContentPage(
            title="Draft Child",
            slug="draft-child",
            live=False,  # Explicitly set as not live
        )
        parent.add_child(instance=draft_child)
        draft_child.save_revision()  # Save but don't publish

        # Create published child
        published_child = ContentPage(
            title="Published Child",
            slug="published-child",
        )
        parent.add_child(instance=published_child)
        published_child.save_revision().publish()

        # Request the parent page - should redirect to published child
        response = self.client.get(parent.url)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == published_child.url

    def test_structure_only_multilevel_redirect(self):
        """Test that structure-only works with multi-level nesting."""
        # Create structure-only parent
        parent = ContentPage(
            title="Parent",
            slug="parent-multilevel",
            is_structure_only=True,
        )
        self.homepage.add_child(instance=parent)
        parent.save_revision().publish()

        # Create structure-only child
        child = ContentPage(
            title="Child Structure",
            slug="child-structure",
            is_structure_only=True,
        )
        parent.add_child(instance=child)
        child.save_revision().publish()

        # Create grandchild (actual content page)
        grandchild = ContentPage(
            title="Grandchild",
            slug="grandchild",
        )
        child.add_child(instance=grandchild)
        grandchild.save_revision().publish()

        # Request the parent - should redirect to child (which will then redirect to
        # grandchild). But our test only checks the first redirect
        response = self.client.get(parent.url)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == child.url

        # Following the redirect chain would eventually lead to grandchild
        # The browser would handle this automatically

    def test_non_structure_only_displays_normally(self):
        """Test that pages without is_structure_only display normally."""
        # Create regular page
        page = ContentPage(
            title="Regular Page",
            slug="regular-page",
            is_structure_only=False,
        )
        self.homepage.add_child(instance=page)
        page.save_revision().publish()

        # Request the page - should display normally
        response = self.client.get(page.url)
        assert response.status_code == HTTPStatus.OK

    def test_structure_only_with_visibility_members(self):
        """Test that visibility check happens before structure-only redirect."""
        User = get_user_model()  # noqa: N806

        # Create members-only structure page
        parent = ContentPage(
            title="Members Structure",
            slug="members-structure",
            is_structure_only=True,
            visibility=ContentPage.VISIBILITY_MEMBERS,
        )
        self.homepage.add_child(instance=parent)
        parent.save_revision().publish()

        # Create child page
        child = ContentPage(
            title="Child",
            slug="child-of-members",
        )
        parent.add_child(instance=child)
        child.save_revision().publish()

        # Anonymous user should get forbidden, not redirected
        response = self.client.get(parent.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        # Superuser should get redirected to child
        user = User.objects.create_superuser(
            username="admin",
            password="pw",
            email="admin@example.com",
        )
        self.client.force_login(user)
        response = self.client.get(parent.url)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == child.url
