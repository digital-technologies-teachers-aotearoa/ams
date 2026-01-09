import pytest
from django.utils import timezone

from ams.organisations.forms import InviteOrganisationMemberForm
from ams.organisations.tests.factories import OrganisationFactory
from ams.organisations.tests.factories import OrganisationMemberFactory
from ams.users.tests.factories import UserFactory


@pytest.mark.django_db
class TestInviteOrganisationMemberForm:
    """Unit tests for InviteOrganisationMemberForm.clean_email() method."""

    def test_clean_email_allows_new_invite(self):
        """Test that form allows inviting a new email address."""
        org = OrganisationFactory()

        form = InviteOrganisationMemberForm(
            organisation=org,
            data={"email": "new@example.com"},
        )

        assert form.is_valid()
        assert form.cleaned_data["email"] == "new@example.com"

    def test_clean_email_rejects_active_member(self):
        """Test that ValidationError is raised for accepted members."""
        org = OrganisationFactory()
        user = UserFactory(email="active@example.com")

        # Create an accepted member
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            invite_email="active@example.com",
            accepted_datetime=timezone.now(),
            declined_datetime=None,
            revoked_datetime=None,
        )

        form = InviteOrganisationMemberForm(
            organisation=org,
            data={"email": "active@example.com"},
        )

        assert not form.is_valid()
        assert "email" in form.errors
        assert "already associated with a member" in str(form.errors["email"])

    def test_clean_email_rejects_pending_invite(self):
        """Test that ValidationError is raised for pending invites."""
        org = OrganisationFactory()

        # Create a pending invite (not accepted, not declined, not revoked)
        OrganisationMemberFactory(
            organisation=org,
            invite_email="pending@example.com",
            accepted_datetime=None,
            declined_datetime=None,
            revoked_datetime=None,
        )

        form = InviteOrganisationMemberForm(
            organisation=org,
            data={"email": "pending@example.com"},
        )

        assert not form.is_valid()
        assert "email" in form.errors
        assert "already associated with a member" in str(form.errors["email"])

    def test_clean_email_normalizes_case(self):
        """Test that email is normalized to lowercase."""
        org = OrganisationFactory()

        form = InviteOrganisationMemberForm(
            organisation=org,
            data={"email": "USER@EXAMPLE.COM"},
        )

        assert form.is_valid()
        assert form.cleaned_data["email"] == "user@example.com"

    def test_clean_email_checks_user_email_field(self):
        """Test that validation checks the user's email, not just invite_email."""
        org = OrganisationFactory()
        user = UserFactory(email="user@example.com")

        # Create an accepted member - user was invited via one email but
        # logged in with a different email (user.email)
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            invite_email="original@example.com",  # Original invite email
            accepted_datetime=timezone.now(),
            declined_datetime=None,
            revoked_datetime=None,
        )

        # Try to invite the user's current email - should be rejected
        form = InviteOrganisationMemberForm(
            organisation=org,
            data={"email": "user@example.com"},
        )

        assert not form.is_valid()
        assert "email" in form.errors

    def test_clean_email_allows_invite_to_different_org(self):
        """Test that same email can be invited to different organisations."""
        org1 = OrganisationFactory()
        org2 = OrganisationFactory()

        # Create pending invite for org1
        OrganisationMemberFactory(
            organisation=org1,
            invite_email="shared@example.com",
            accepted_datetime=None,
            declined_datetime=None,
            revoked_datetime=None,
        )

        # Should be able to invite same email to org2
        form = InviteOrganisationMemberForm(
            organisation=org2,
            data={"email": "shared@example.com"},
        )

        assert form.is_valid()
