"""Tests for terms admin interfaces."""

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import Client
from django.test import RequestFactory

from ams.terms.admin import TermVersionAdmin
from ams.terms.models import TermVersion

from .factories import TermAcceptanceFactory
from .factories import TermFactory
from .factories import TermVersionFactory

pytestmark = pytest.mark.django_db


class TestTermVersionAdminDeletion:
    """Test deletion handling in TermVersion admin."""

    def test_delete_without_acceptances_succeeds(self):
        """Deletion should succeed when no acceptances exist."""
        term = TermFactory()
        version = TermVersionFactory(term=term)
        admin = TermVersionAdmin(TermVersion, AdminSite())
        request = RequestFactory().post("/")

        admin.delete_model(request, version)
        assert not TermVersion.objects.filter(pk=version.pk).exists()

    def test_delete_with_acceptances_shows_error(self):
        """Deletion should be prevented with error message when acceptances exist."""
        term = TermFactory()
        version = TermVersionFactory(term=term)
        TermAcceptanceFactory(term_version=version)

        admin = TermVersionAdmin(TermVersion, AdminSite())
        request = RequestFactory().post("/")
        request.session = {}
        messages = FallbackStorage(request)
        request._messages = messages  # noqa: SLF001

        admin.delete_model(request, version)

        # Should still exist
        assert TermVersion.objects.filter(pk=version.pk).exists()

        # Should have error message
        message_list = list(messages)
        assert len(message_list) > 0
        assert "audit history" in str(message_list[0])

    def test_bulk_delete_partial_success(self):
        """Bulk deletion should handle mix of deletable and protected versions."""
        term = TermFactory()
        deletable1 = TermVersionFactory(term=term, version="1.0")
        deletable2 = TermVersionFactory(term=term, version="2.0")
        protected = TermVersionFactory(term=term, version="3.0")
        TermAcceptanceFactory(term_version=protected)

        admin = TermVersionAdmin(TermVersion, AdminSite())
        request = RequestFactory().post("/")
        request.session = {}
        messages = FallbackStorage(request)
        request._messages = messages  # noqa: SLF001

        queryset = TermVersion.objects.filter(
            pk__in=[deletable1.pk, deletable2.pk, protected.pk],
        )
        admin.delete_queryset(request, queryset)

        # Two should be deleted
        assert not TermVersion.objects.filter(pk=deletable1.pk).exists()
        assert not TermVersion.objects.filter(pk=deletable2.pk).exists()

        # One should still exist
        assert TermVersion.objects.filter(pk=protected.pk).exists()

        # Should have both success and error messages
        message_list = list(messages)
        expected_messages = 2
        assert len(message_list) == expected_messages

    def test_delete_view_no_success_message_on_failure(self):
        """Verify delete_view doesn't show success when deletion fails."""
        term = TermFactory()
        version = TermVersionFactory(term=term)
        TermAcceptanceFactory(term_version=version)

        User = get_user_model()  # noqa: N806
        admin_user = User.objects.create_superuser(
            email="admin@test.com",
            password="password",  # noqa: S106
        )

        client = Client()
        client.force_login(admin_user)

        # POST to delete view
        url = f"/admin/terms/termversion/{version.pk}/delete/"
        response = client.post(url, {"post": "yes"}, follow=True)

        # Check messages
        messages_list = list(response.context["messages"])

        # Should have ERROR message
        error_messages = [m for m in messages_list if m.level_tag == "error"]
        assert len(error_messages) == 1
        assert "audit history" in str(error_messages[0])

        # Should NOT have SUCCESS message
        success_messages = [m for m in messages_list if m.level_tag == "success"]
        assert len(success_messages) == 0, "Should not show success when deletion fails"

        # Object should still exist
        assert TermVersion.objects.filter(pk=version.pk).exists()
