"""Tests for membership admin interfaces."""

import pytest
from django.contrib.admin.sites import AdminSite

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
