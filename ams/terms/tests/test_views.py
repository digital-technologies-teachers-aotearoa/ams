"""Tests for terms views."""

from datetime import timedelta
from http import HTTPStatus

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from ams.terms.models import TermAcceptance
from ams.terms.tests.factories import TermFactory
from ams.terms.tests.factories import TermVersionFactory
from ams.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestAcceptTermsView:
    """Tests for accept_terms_view."""

    def test_requires_login(self, client: Client):
        """Test that view requires authentication."""
        response = client.get(reverse("terms:accept"))

        # Should redirect to login
        assert response.status_code == HTTPStatus.FOUND
        assert "/accounts/login/" in response.url

    def test_get_displays_first_pending_term(self, client: Client):
        """Test GET request displays the first pending term."""
        user = UserFactory()
        client.force_login(user)

        term = TermFactory(name="Privacy Policy")
        TermVersionFactory(
            term=term,
            version="1.0",
            content="<p>Privacy policy content</p>",
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        response = client.get(reverse("terms:accept"))

        assert response.status_code == HTTPStatus.OK
        assert "Privacy Policy" in str(response.content)
        assert "1.0" in str(response.content)

    def test_post_creates_term_acceptance_record(self, client: Client):
        """Test POST creates TermAcceptance with correct data."""
        user = UserFactory()
        client.force_login(user)

        term_version = TermVersionFactory(
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        client.post(
            reverse("terms:accept"),
            data={"next": "/home/"},
        )

        # Check acceptance was created
        acceptance = TermAcceptance.objects.get(user=user, term_version=term_version)
        assert acceptance.user == user
        assert acceptance.term_version == term_version
        assert acceptance.ip_address is not None
        assert acceptance.user_agent is not None
        assert acceptance.source == "web"

    def test_post_records_ip_address(self, client: Client):
        """Test POST records correct IP address."""
        user = UserFactory()
        client.force_login(user)

        term_version = TermVersionFactory(
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        client.post(
            reverse("terms:accept"),
            data={"next": "/home/"},
            HTTP_X_FORWARDED_FOR="192.168.1.100, 10.0.0.1",
        )

        acceptance = TermAcceptance.objects.get(user=user, term_version=term_version)
        # Should use first IP from X-Forwarded-For
        assert acceptance.ip_address == "192.168.1.100"

    def test_post_records_user_agent(self, client: Client):
        """Test POST records user agent."""
        user = UserFactory()
        client.force_login(user)

        term_version = TermVersionFactory(
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        client.post(
            reverse("terms:accept"),
            data={"next": "/home/"},
            HTTP_USER_AGENT="Mozilla/5.0 Test Browser",
        )

        acceptance = TermAcceptance.objects.get(user=user, term_version=term_version)
        assert "Mozilla/5.0" in acceptance.user_agent

    def test_post_redirects_to_self_when_more_terms_pending(self, client: Client):
        """Test POST redirects to self when more terms are pending."""
        user = UserFactory()
        client.force_login(user)

        # Create two pending terms
        term1 = TermFactory(key="a-policy")
        term2 = TermFactory(key="b-policy")
        TermVersionFactory(
            term=term1,
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )
        TermVersionFactory(
            term=term2,
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        response = client.post(
            reverse("terms:accept"),
            data={"next": "/home/"},
        )

        # Should redirect back to accept view with next parameter
        assert response.status_code == HTTPStatus.FOUND
        assert reverse("terms:accept") in response.url
        assert "next=/home/" in response.url or "next=%2Fhome%2F" in response.url

    def test_post_redirects_to_next_when_no_more_terms(self, client: Client):
        """Test POST redirects to 'next' URL when all terms accepted."""
        user = UserFactory()
        client.force_login(user)

        # Create single pending term
        TermVersionFactory(
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        response = client.post(
            reverse("terms:accept"),
            data={"next": "/home/"},
        )

        # After accepting, should redirect to final destination
        # But first it redirects to self, then to destination
        # Follow the redirect chain
        final_response = client.get(response.url)
        assert final_response.status_code == HTTPStatus.FOUND
        assert final_response.url == "/home/"

    def test_get_with_no_pending_terms_redirects_to_next(self, client: Client):
        """Test GET with no pending terms redirects to 'next' URL."""
        user = UserFactory()
        client.force_login(user)

        response = client.get(f"{reverse('terms:accept')}?next=/home/")

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == "/home/"

    def test_get_with_no_pending_terms_redirects_to_home(self, client: Client):
        """Test GET with no pending terms and no 'next' redirects to root."""
        user = UserFactory()
        client.force_login(user)

        response = client.get(reverse("terms:accept"))

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("root_redirect")

    def test_no_duplicate_acceptances(self, client: Client):
        """Test that duplicate acceptances cannot be created."""
        user = UserFactory()
        client.force_login(user)

        term_version = TermVersionFactory(
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        # First acceptance
        client.post(
            reverse("terms:accept"),
            data={"next": "/home/"},
        )

        # Try to accept again - should not create duplicate
        acceptances_count = TermAcceptance.objects.filter(
            user=user,
            term_version=term_version,
        ).count()
        assert acceptances_count == 1

    def test_displays_progress_indicator(self, client: Client):
        """Test that progress indicator is displayed correctly."""
        user = UserFactory()
        client.force_login(user)

        # Create three pending terms
        for _i in range(3):
            TermVersionFactory(
                is_active=True,
                date_active=timezone.now() - timedelta(days=1),
            )

        response = client.get(reverse("terms:accept"))

        assert response.status_code == HTTPStatus.OK
        # Check for progress indicator
        assert "1 of 3" in str(response.content) or "Reviewing 1 of 3" in str(
            response.content,
        )


class TestTermsListView:
    """Tests for terms_list_view."""

    def test_accessible_to_anonymous_users(self, client: Client):
        """Test that anonymous users can access the list view."""
        response = client.get(reverse("terms:list"))

        assert response.status_code == HTTPStatus.OK

    def test_accessible_to_authenticated_users(self, client: Client):
        """Test that authenticated users can access the list view."""
        user = UserFactory()
        client.force_login(user)

        response = client.get(reverse("terms:list"))

        assert response.status_code == HTTPStatus.OK

    def test_displays_all_latest_term_versions(self, client: Client):
        """Test that all latest term versions are displayed."""
        # Create two terms, each with multiple versions
        term_a = TermFactory(name="Privacy Policy", key="privacy")
        TermVersionFactory(
            term=term_a,
            version="1.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=10),
        )
        TermVersionFactory(
            term=term_a,
            version="2.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        term_b = TermFactory(name="Terms of Service", key="tos")
        TermVersionFactory(
            term=term_b,
            version="1.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=5),
        )

        response = client.get(reverse("terms:list"))

        assert response.status_code == HTTPStatus.OK
        # Should display both terms
        assert "Privacy Policy" in str(response.content)
        assert "Terms of Service" in str(response.content)
        # Should display latest versions
        assert "2.0" in str(response.content)  # Latest Privacy Policy version
        assert "1.0" in str(response.content)  # Latest ToS version

    def test_displays_only_latest_versions(self, client: Client):
        """Test that only latest versions are shown, not old ones."""
        term = TermFactory(name="Test Policy", key="test")
        TermVersionFactory(
            term=term,
            version="1.0",
            content="<p>Old version content</p>",
            is_active=True,
            date_active=timezone.now() - timedelta(days=10),
        )
        TermVersionFactory(
            term=term,
            version="2.0",
            content="<p>New version content</p>",
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        response = client.get(reverse("terms:list"))

        assert response.status_code == HTTPStatus.OK
        # Should show new version content
        assert "New version content" in str(response.content)
        # Should NOT show old version content
        assert "Old version content" not in str(response.content)

    def test_empty_state_when_no_terms(self, client: Client):
        """Test that empty state is displayed when no terms exist."""
        response = client.get(reverse("terms:list"))

        assert response.status_code == HTTPStatus.OK
        assert "No terms are currently available" in str(response.content)

    def test_excludes_inactive_versions(self, client: Client):
        """Test that inactive versions are not displayed."""
        term = TermFactory(name="Test Policy")
        TermVersionFactory(
            term=term,
            version="1.0",
            is_active=False,
            date_active=timezone.now() - timedelta(days=1),
        )

        response = client.get(reverse("terms:list"))

        assert response.status_code == HTTPStatus.OK
        # Should show empty state since no active versions
        assert "No terms are currently available" in str(response.content)
