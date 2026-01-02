import pytest
from django.utils import timezone

from ams.organisations.models import OrganisationMember
from ams.organisations.tests.factories import OrganisationMemberFactory


@pytest.mark.django_db
class TestOrganisationMember:
    """Test class for OrganisationMember model."""

    def test_role_can_be_admin(self):
        """Test that role field can be set to ADMIN."""
        member = OrganisationMemberFactory(admin=True)
        assert member.role == OrganisationMember.Role.ADMIN

    def test_is_active_accepted_and_user_active(self):
        """Test is_active returns True for accepted members with active users."""
        member = OrganisationMemberFactory(
            accepted_datetime=timezone.now(),
            user__is_active=True,
        )
        assert member.is_active() is True

    def test_is_active_not_accepted(self):
        """Test is_active returns False for members who haven't accepted."""
        member = OrganisationMemberFactory(accepted_datetime=None)
        assert member.is_active() is False

    def test_is_active_user_inactive(self):
        """Test is_active returns False for accepted members with inactive users."""
        member = OrganisationMemberFactory(
            accepted_datetime=timezone.now(),
            user__is_active=False,
        )
        assert member.is_active() is False

    def test_str_with_user(self):
        """Test string representation with a user shows user's full name."""
        member = OrganisationMemberFactory(
            user__first_name="John",
            user__last_name="Doe",
        )
        assert str(member) == "John Doe"

    def test_str_with_invite_only(self):
        """Test string representation with invite shows email and org name."""
        member = OrganisationMemberFactory(
            user=None,
            invite_email="test@example.com",
            organisation__name="Test Corp",
        )
        result = str(member)
        assert "test@example.com" in result
        assert "Test Corp" in result
        assert "Invite Pending" in result
