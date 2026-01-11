"""Tests for terms models."""

from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.utils import timezone

from ams.terms.models import TermAcceptance
from ams.terms.tests.factories import TermAcceptanceFactory
from ams.terms.tests.factories import TermFactory
from ams.terms.tests.factories import TermVersionFactory
from ams.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestTerm:
    """Tests for Term model."""

    def test_term_creation(self):
        """Test that a Term can be created successfully."""
        term = TermFactory(key="privacy-policy", name="Privacy Policy")
        assert term.key == "privacy-policy"
        assert term.name == "Privacy Policy"
        assert str(term) == "Privacy Policy"

    def test_term_key_unique(self):
        """Test that Term key must be unique."""
        TermFactory(key="privacy-policy")
        with pytest.raises(IntegrityError):
            TermFactory(key="privacy-policy")


class TestTermVersion:
    """Tests for TermVersion model."""

    def test_term_version_creation(self):
        """Test that a TermVersion can be created successfully."""
        term = TermFactory(name="Privacy Policy")
        version = TermVersionFactory(
            term=term,
            version="1.0",
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )
        assert version.term == term
        assert version.version == "1.0"
        assert str(version) == "Privacy Policy v1.0"

    def test_term_version_unique_constraint(self):
        """Test that term + version combination must be unique."""
        term = TermFactory()
        TermVersionFactory(term=term, version="1.0")
        with pytest.raises(IntegrityError):
            TermVersionFactory(term=term, version="1.0")

    def test_is_current_active_and_past_date(self):
        """Test is_current() returns True for active version with past date."""
        version = TermVersionFactory(
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )
        assert version.is_current() is True

    def test_is_current_inactive(self):
        """Test is_current() returns False for inactive version."""
        version = TermVersionFactory(
            is_active=False,
            date_active=timezone.now() - timedelta(days=1),
        )
        assert version.is_current() is False

    def test_is_current_future_date(self):
        """Test is_current() returns False for future-dated version."""
        version = TermVersionFactory(
            is_active=True,
            date_active=timezone.now() + timedelta(days=1),
        )
        assert version.is_current() is False

    def test_is_current_active_and_current_date(self):
        """Test is_current() returns True for active version with current date."""
        version = TermVersionFactory(
            is_active=True,
            date_active=timezone.now() - timedelta(seconds=1),
        )
        assert version.is_current() is True

    def test_cannot_delete_term_with_versions(self):
        """Test that Term cannot be deleted if it has TermVersions (PROTECT)."""
        term = TermFactory()
        TermVersionFactory(term=term)
        with pytest.raises(ProtectedError):
            term.delete()


class TestTermAcceptance:
    """Tests for TermAcceptance model."""

    def test_term_acceptance_creation(self):
        """Test that a TermAcceptance can be created successfully."""
        user = UserFactory()
        term_version = TermVersionFactory()
        acceptance = TermAcceptanceFactory(
            user=user,
            term_version=term_version,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )
        assert acceptance.user == user
        assert acceptance.term_version == term_version
        assert acceptance.ip_address == "192.168.1.1"
        assert "Mozilla/5.0" in acceptance.user_agent
        assert acceptance.source == "web"

    def test_term_acceptance_unique_constraint(self):
        """Test that user + term_version combination must be unique."""
        user = UserFactory()
        term_version = TermVersionFactory()
        TermAcceptanceFactory(user=user, term_version=term_version)
        with pytest.raises(IntegrityError):
            TermAcceptanceFactory(user=user, term_version=term_version)

    def test_cannot_delete_term_version_with_acceptances(self):
        """Test that TermVersion cannot be deleted if accepted (PROTECT)."""
        term_version = TermVersionFactory()
        TermAcceptanceFactory(term_version=term_version)
        with pytest.raises(ProtectedError):
            term_version.delete()

    def test_acceptance_deleted_when_user_deleted(self):
        """Test that TermAcceptance is deleted when user is deleted (CASCADE)."""
        user = UserFactory()
        acceptance = TermAcceptanceFactory(user=user)
        acceptance_id = acceptance.id

        user.delete()

        assert not TermAcceptance.objects.filter(id=acceptance_id).exists()
