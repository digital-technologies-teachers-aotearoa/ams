"""Tests for membership admin interfaces."""

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import Client
from django.test import RequestFactory

from ams.memberships.admin import IndividualMembershipAdmin
from ams.memberships.admin import MembershipOptionAdmin
from ams.memberships.models import IndividualMembership
from ams.memberships.models import MembershipOption

from .factories import IndividualMembershipFactory
from .factories import MembershipOptionFactory

pytestmark = pytest.mark.django_db


class TestIndividualMembershipAdmin:
    def test_list_display_with_valid_membership(self):
        """Test that admin list_display works with a valid membership."""
        # Arrange
        membership = IndividualMembershipFactory()
        admin = IndividualMembershipAdmin(IndividualMembership, AdminSite())

        # Act & Assert - should not raise any errors
        assert admin.user_display(membership) is not None
        assert admin.status(membership) is not None

    def test_list_display_with_none_expiry_date(self):
        """Test that admin list_display handles None expiry_date gracefully.

        This test verifies the fix for the TypeError that occurred when
        expiry_date was None and the status() method tried to call is_expired().

        Note: While the database has a NOT NULL constraint, this test ensures
        the code is defensive in case data corruption or direct SQL operations
        bypass normal validation.
        """
        # Arrange
        membership = IndividualMembershipFactory()
        # Set expiry_date to None without saving to test the method's defensiveness
        membership.expiry_date = None
        admin = IndividualMembershipAdmin(IndividualMembership, AdminSite())

        # Act & Assert - should not raise TypeError
        status = admin.status(membership)
        assert status is not None

    def test_list_display_with_expired_membership(self):
        """Test that admin correctly displays expired memberships."""
        # Arrange
        membership = IndividualMembershipFactory(expired=True)
        admin = IndividualMembershipAdmin(IndividualMembership, AdminSite())

        # Act
        status = admin.status(membership)

        # Assert
        assert "Expired" in status


class TestMembershipOptionAdmin:
    def test_archived_field_accessible_on_creation(self):
        """Test that archived field is accessible when creating a MembershipOption."""
        # Arrange
        admin = MembershipOptionAdmin(MembershipOption, AdminSite())
        request = None  # Request is not used by get_fieldsets in this case

        # Act
        fieldsets = admin.get_fieldsets(request, obj=None)

        # Assert - archived field should be present in the fieldsets
        all_fields = []
        for _name, options in fieldsets:
            all_fields.extend(options.get("fields", []))

        assert "archived" in all_fields, (
            "archived field should be accessible on creation"
        )

    def test_archived_field_accessible_on_update(self):
        """Test that archived field is accessible when updating a MembershipOption."""
        # Arrange
        membership_option = MembershipOptionFactory()
        admin = MembershipOptionAdmin(MembershipOption, AdminSite())
        request = None  # Request is not used by get_fieldsets in this case

        # Act
        fieldsets = admin.get_fieldsets(request, obj=membership_option)

        # Assert - archived field should be present in the fieldsets
        all_fields = []
        for _name, options in fieldsets:
            all_fields.extend(options.get("fields", []))

        assert "archived" in all_fields, "archived field should be accessible on update"


class TestMembershipOptionAdminDeletion:
    """Test deletion handling in MembershipOption admin."""

    def test_delete_without_memberships_succeeds(self):
        """Deletion should succeed when no memberships exist."""
        option = MembershipOptionFactory()
        admin = MembershipOptionAdmin(MembershipOption, AdminSite())
        request = RequestFactory().post("/")

        # Should not raise
        admin.delete_model(request, option)
        assert not MembershipOption.objects.filter(pk=option.pk).exists()

    def test_delete_with_individual_membership_shows_error(self):
        """Deletion should be prevented with error message when individual memberships
        exist."""
        option = MembershipOptionFactory()
        IndividualMembershipFactory(membership_option=option)
        admin = MembershipOptionAdmin(MembershipOption, AdminSite())

        request = RequestFactory().post("/")
        # Add messages middleware
        request.session = {}
        messages = FallbackStorage(request)
        request._messages = messages  # noqa: SLF001

        admin.delete_model(request, option)

        # Should still exist
        assert MembershipOption.objects.filter(pk=option.pk).exists()

        # Should have error message
        message_list = list(messages)
        assert len(message_list) > 0
        assert "Archive it instead" in str(message_list[0])

    def test_bulk_delete_partial_success(self):
        """Bulk deletion should handle mix of deletable and protected options."""
        deletable1 = MembershipOptionFactory()
        deletable2 = MembershipOptionFactory()
        protected = MembershipOptionFactory()
        IndividualMembershipFactory(membership_option=protected)

        admin = MembershipOptionAdmin(MembershipOption, AdminSite())

        request = RequestFactory().post("/")
        request.session = {}
        messages = FallbackStorage(request)
        request._messages = messages  # noqa: SLF001

        queryset = MembershipOption.objects.filter(
            pk__in=[deletable1.pk, deletable2.pk, protected.pk],
        )
        admin.delete_queryset(request, queryset)

        # Two should be deleted
        assert not MembershipOption.objects.filter(pk=deletable1.pk).exists()
        assert not MembershipOption.objects.filter(pk=deletable2.pk).exists()

        # One should still exist
        assert MembershipOption.objects.filter(pk=protected.pk).exists()

        # Should have both success and error messages
        message_list = list(messages)
        expected_messages = 2
        assert len(message_list) == expected_messages

    def test_delete_view_no_success_message_on_failure(self):
        """Verify delete_view doesn't show success when deletion fails."""
        option = MembershipOptionFactory()
        IndividualMembershipFactory(membership_option=option)

        # Use Django test client to call delete_view

        User = get_user_model()  # noqa: N806
        admin_user = User.objects.create_superuser(
            email="admin@test.com",
            password="password",  # noqa: S106
        )

        client = Client()
        client.force_login(admin_user)

        # POST to delete view
        url = f"/admin/memberships/membershipoption/{option.pk}/delete/"
        response = client.post(url, {"post": "yes"}, follow=True)

        # Check messages
        messages_list = list(response.context["messages"])

        # Should have ERROR message
        error_messages = [m for m in messages_list if m.level_tag == "error"]
        assert len(error_messages) == 1
        assert "Archive it instead" in str(error_messages[0])

        # Should NOT have SUCCESS message
        success_messages = [m for m in messages_list if m.level_tag == "success"]
        assert len(success_messages) == 0, "Should not show success when deletion fails"

        # Object should still exist
        assert MembershipOption.objects.filter(pk=option.pk).exists()
