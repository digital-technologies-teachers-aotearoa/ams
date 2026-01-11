"""Tests for terms decorators."""

from datetime import timedelta
from http import HTTPStatus
from unittest.mock import Mock

import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from django.utils import timezone

from ams.terms.decorators import terms_required
from ams.terms.tests.factories import TermAcceptanceFactory
from ams.terms.tests.factories import TermVersionFactory
from ams.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestTermsRequiredDecorator:
    """Tests for @terms_required decorator."""

    def test_allows_access_when_no_pending_terms(self, rf: RequestFactory):
        """Test that access is allowed when user has no pending terms."""

        @terms_required
        def test_view(request):
            return HttpResponse("OK")

        user = UserFactory()
        request = rf.get("/test/")
        request.user = user

        response = test_view(request)

        assert response.status_code == HTTPStatus.OK
        assert response.content == b"OK"

    def test_redirects_when_pending_terms_exist(self, rf: RequestFactory):
        """Test that user is redirected when pending terms exist."""

        @terms_required
        def test_view(request):
            return HttpResponse("OK")

        user = UserFactory()

        # Create a pending term version
        TermVersionFactory(
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        request = rf.get("/test/path/")
        request.user = user

        response = test_view(request)

        assert response.status_code == HTTPStatus.FOUND
        assert "/en/terms/accept/" in response.url
        assert "next=%2Ftest%2Fpath%2F" in response.url

    def test_preserves_next_parameter(self, rf: RequestFactory):
        """Test that original URL is preserved in 'next' parameter."""

        @terms_required
        def test_view(request):
            return HttpResponse("OK")

        user = UserFactory()

        TermVersionFactory(
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        request = rf.get("/original/destination/")
        request.user = user

        response = test_view(request)

        assert "next=%2Foriginal%2Fdestination%2F" in response.url

    def test_does_not_block_anonymous_users(self, rf: RequestFactory):
        """Test that anonymous users are not blocked (requirement)."""

        @terms_required
        def test_view(request):
            return HttpResponse("OK")

        TermVersionFactory(
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        request = rf.get("/test/")
        request.user = Mock(is_authenticated=False)

        response = test_view(request)

        # Anonymous users pass through
        assert response.status_code == HTTPStatus.OK

    def test_allows_access_when_terms_already_accepted(self, rf: RequestFactory):
        """Test that access is allowed when user has already accepted terms."""

        @terms_required
        def test_view(request):
            return HttpResponse("OK")

        user = UserFactory()
        term_version = TermVersionFactory(
            is_active=True,
            date_active=timezone.now() - timedelta(days=1),
        )

        # User has accepted this version
        TermAcceptanceFactory(user=user, term_version=term_version)

        request = rf.get("/test/")
        request.user = user

        response = test_view(request)

        assert response.status_code == HTTPStatus.OK
        assert response.content == b"OK"
