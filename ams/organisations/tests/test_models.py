import pytest
from django.utils import timezone

from ams.memberships.tests.factories import OrganisationMembershipFactory
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


@pytest.mark.django_db
class TestOrganisationMemberQuerySet:
    """Test OrganisationMemberQuerySet methods."""

    def test_active_filters_declined_members(self):
        """Test that declined members are excluded from active()."""
        org = OrganisationMemberFactory().organisation
        active_member = OrganisationMemberFactory(organisation=org)
        declined_member = OrganisationMemberFactory(
            organisation=org,
            declined_datetime=timezone.now(),
        )

        active_members = org.organisation_members.active()

        assert active_member in active_members
        assert declined_member not in active_members

    def test_active_filters_revoked_members(self):
        """Test that revoked members are excluded from active()."""
        org = OrganisationMemberFactory().organisation
        active_member = OrganisationMemberFactory(organisation=org)
        revoked_member = OrganisationMemberFactory(
            organisation=org,
            revoked_datetime=timezone.now(),
        )

        active_members = org.organisation_members.active()

        assert active_member in active_members
        assert revoked_member not in active_members

    def test_admins_filters_by_role(self):
        """Test that only ADMIN role members are returned by admins()."""
        org = OrganisationMemberFactory().organisation
        admin_member = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.ADMIN,
        )
        regular_member = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
        )

        admins = org.organisation_members.admins()

        assert admin_member in admins
        assert regular_member not in admins

    def test_active_admins_combines_filters(self):
        """Test chaining active() and admins() works correctly."""
        org = OrganisationMemberFactory().organisation
        active_admin = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.ADMIN,
        )
        declined_admin = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.ADMIN,
            declined_datetime=timezone.now(),
        )
        active_member = OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
        )

        active_admins = org.organisation_members.active_admins()

        assert active_admin in active_admins
        assert declined_admin not in active_admins
        assert active_member not in active_admins

    def test_for_organisation_filters_correctly(self):
        """Test for_organisation() filters by organisation."""
        org1 = OrganisationMemberFactory().organisation
        org2 = OrganisationMemberFactory().organisation
        member1 = OrganisationMemberFactory(organisation=org1)
        member2 = OrganisationMemberFactory(organisation=org2)

        org1_members = OrganisationMember.objects.for_organisation(org1)

        assert member1 in org1_members
        assert member2 not in org1_members


@pytest.mark.django_db
class TestOrganisationHelperMethods:
    """Test Organisation model helper methods."""

    def test_get_active_membership_returns_active(self):
        """Test returns active membership when exists."""
        org = OrganisationMemberFactory().organisation
        active_membership = OrganisationMembershipFactory(
            organisation=org,
            active=True,
        )

        result = org.get_active_membership()

        assert result == active_membership

    def test_get_active_membership_returns_none_when_no_membership(self):
        """Test returns None when no active membership exists."""
        org = OrganisationMemberFactory().organisation

        result = org.get_active_membership()

        assert result is None

    def test_get_active_membership_ignores_cancelled(self):
        """Test cancelled memberships are not returned."""
        org = OrganisationMemberFactory().organisation
        OrganisationMembershipFactory(
            organisation=org,
            cancelled=True,
        )

        result = org.get_active_membership()

        assert result is None

    def test_get_active_membership_ignores_expired(self):
        """Test expired memberships are not returned."""
        org = OrganisationMemberFactory().organisation
        OrganisationMembershipFactory(
            organisation=org,
            expired=True,
        )

        result = org.get_active_membership()

        assert result is None

    def test_has_minimum_admin_count_with_enough_admins(self):
        """Test returns True when org has sufficient admins."""
        org = OrganisationMemberFactory().organisation
        OrganisationMemberFactory(organisation=org, admin=True)
        OrganisationMemberFactory(organisation=org, admin=True)

        assert org.has_minimum_admin_count(minimum=1) is True
        assert org.has_minimum_admin_count(minimum=2) is True

    def test_has_minimum_admin_count_with_insufficient_admins(self):
        """Test returns False when org has insufficient admins."""
        org = OrganisationMemberFactory().organisation
        OrganisationMemberFactory(organisation=org, admin=True)

        assert org.has_minimum_admin_count(minimum=2) is False

    def test_has_minimum_admin_count_excludes_declined(self):
        """Test declined admin members are not counted."""
        org = OrganisationMemberFactory().organisation
        OrganisationMemberFactory(
            organisation=org,
            admin=True,
            declined_datetime=timezone.now(),
        )

        assert org.has_minimum_admin_count(minimum=1) is False

    def test_has_minimum_admin_count_excludes_revoked(self):
        """Test revoked admin members are not counted."""
        org = OrganisationMemberFactory().organisation
        OrganisationMemberFactory(
            organisation=org,
            admin=True,
            revoked_datetime=timezone.now(),
        )

        assert org.has_minimum_admin_count(minimum=1) is False

    def test_has_minimum_admin_count_default_minimum_is_one(self):
        """Test default minimum parameter value is 1."""
        org = OrganisationMemberFactory().organisation
        OrganisationMemberFactory(organisation=org, admin=True)

        assert org.has_minimum_admin_count() is True

    def test_has_minimum_admin_count_excludes_regular_members(self):
        """Test regular members are not counted as admins."""
        org = OrganisationMemberFactory().organisation
        OrganisationMemberFactory(
            organisation=org,
            role=OrganisationMember.Role.MEMBER,
        )

        assert org.has_minimum_admin_count(minimum=1) is False

    def test_has_active_membership_property_returns_true(self):
        """Test property returns True when org has active membership."""
        org = OrganisationMemberFactory().organisation
        OrganisationMembershipFactory(
            organisation=org,
            active=True,
        )

        assert org.has_active_membership is True

    def test_has_active_membership_property_returns_false(self):
        """Test property returns False when no active membership."""
        org = OrganisationMemberFactory().organisation

        assert org.has_active_membership is False

    def test_has_active_membership_excludes_cancelled(self):
        """Test cancelled memberships are not considered active."""
        org = OrganisationMemberFactory().organisation
        OrganisationMembershipFactory(
            organisation=org,
            cancelled=True,
        )

        assert org.has_active_membership is False

    def test_has_active_membership_excludes_expired(self):
        """Test expired memberships are not considered active."""
        org = OrganisationMemberFactory().organisation
        OrganisationMembershipFactory(
            organisation=org,
            expired=True,
        )

        assert org.has_active_membership is False
