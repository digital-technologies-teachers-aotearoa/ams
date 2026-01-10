from http import HTTPStatus

import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from ams.organisations.tests.factories import OrganisationFactory
from ams.organisations.tests.factories import OrganisationMemberFactory
from ams.users.models import User
from ams.users.tests.factories import UserFactory
from ams.users.views import user_detail_view

pytestmark = pytest.mark.django_db


class TestUserDetailView:
    def test_user_can_view_own_profile(self, user: User, rf: RequestFactory):
        """Test authenticated user can view their own profile."""
        request = rf.get("/fake-url/")
        request.user = user
        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK

    def test_user_cannot_view_other_profile(self, user: User, rf: RequestFactory):
        """Test user cannot view another user's profile."""
        other_user = UserFactory()
        request = rf.get("/fake-url/")
        request.user = other_user

        with pytest.raises(PermissionDenied):
            user_detail_view(request, username=user.username)

    def test_staff_can_view_any_profile(self, user: User, rf: RequestFactory):
        """Test staff can view any user's profile."""
        staff_user = UserFactory(is_staff=True)
        request = rf.get("/fake-url/")
        request.user = staff_user
        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK

    def test_superuser_can_view_any_profile(self, user: User, rf: RequestFactory):
        """Test superuser can view any user's profile."""
        superuser = UserFactory(is_superuser=True)
        request = rf.get("/fake-url/")
        request.user = superuser
        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK

    def test_not_authenticated(self, user: User, rf: RequestFactory):
        """Test unauthenticated users are redirected to login."""
        request = rf.get("/fake-url/")
        request.user = AnonymousUser()
        response = user_detail_view(request, username=user.username)
        login_url = reverse(settings.LOGIN_URL)

        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == f"{login_url}?next=/fake-url/"

    def test_shows_pending_invites_sent_to_email_before_signup(
        self,
        user: User,
        rf: RequestFactory,
    ):
        """Test that pending invites sent to user's email before signup are shown."""
        organisation = OrganisationFactory()

        # Create an invite to the user's email (simulating invite before signup)
        invite = OrganisationMemberFactory(
            invite=True,  # Sets user=None
            invite_email=user.email,
            organisation=organisation,
        )

        request = rf.get("/fake-url/")
        request.user = user
        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK
        # Check that the invite appears in the context
        pending_invitations = list(
            response.context_data["pending_invitation_table"].data,
        )
        assert len(pending_invitations) == 1
        assert pending_invitations[0].uuid == invite.uuid
        assert response.context_data["has_pending_invitations"] is True

    def test_shows_pending_invites_case_insensitive_email(
        self,
        user: User,
        rf: RequestFactory,
    ):
        """Test that pending invites match user email case-insensitively."""
        organisation = OrganisationFactory()

        # Create an invite with different case email
        invite = OrganisationMemberFactory(
            invite=True,
            invite_email=user.email.upper(),  # Different case
            organisation=organisation,
        )

        request = rf.get("/fake-url/")
        request.user = user
        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK
        pending_invitations = list(
            response.context_data["pending_invitation_table"].data,
        )
        assert len(pending_invitations) == 1
        assert pending_invitations[0].uuid == invite.uuid

    def test_shows_both_user_linked_and_email_linked_invites(
        self,
        user: User,
        rf: RequestFactory,
    ):
        """Test that both user-linked and email-linked pending invites are shown."""
        org1 = OrganisationFactory()
        org2 = OrganisationFactory()

        # Create a user-linked invite (normal flow - user existed when invited)
        user_linked_invite = OrganisationMemberFactory(
            user=user,
            invite_email=user.email,
            organisation=org1,
        )

        # Create an email-linked invite (user didn't exist when invited)
        email_linked_invite = OrganisationMemberFactory(
            invite=True,  # user=None
            invite_email=user.email,
            organisation=org2,
        )

        request = rf.get("/fake-url/")
        request.user = user
        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK
        pending_invitations = list(
            response.context_data["pending_invitation_table"].data,
        )
        expected_invitations = 2
        assert len(pending_invitations) == expected_invitations
        invite_uuids = {invite.uuid for invite in pending_invitations}
        assert user_linked_invite.uuid in invite_uuids
        assert email_linked_invite.uuid in invite_uuids

    def test_does_not_show_declined_or_revoked_email_invites(
        self,
        user: User,
        rf: RequestFactory,
    ):
        """Test that declined/revoked invites sent to email are not shown."""
        org1 = OrganisationFactory()
        org2 = OrganisationFactory()
        org3 = OrganisationFactory()

        # Create a pending invite (should be shown)
        pending_invite = OrganisationMemberFactory(
            invite=True,
            invite_email=user.email,
            organisation=org1,
        )

        # Create a declined invite (should NOT be shown)
        OrganisationMemberFactory(
            invite=True,
            invite_email=user.email,
            organisation=org2,
            declined_datetime=timezone.now(),
        )

        # Create a revoked invite (should NOT be shown)
        OrganisationMemberFactory(
            invite=True,
            invite_email=user.email,
            organisation=org3,
            revoked_datetime=timezone.now(),
        )

        request = rf.get("/fake-url/")
        request.user = user
        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK
        pending_invitations = list(
            response.context_data["pending_invitation_table"].data,
        )
        # Only the pending invite should be shown
        assert len(pending_invitations) == 1
        assert pending_invitations[0].uuid == pending_invite.uuid

    def test_shows_accepted_organisations_from_email_invites(
        self,
        user: User,
        rf: RequestFactory,
    ):
        """Test that accepted organisations from email invites are shown."""
        organisation = OrganisationFactory()

        # Create an accepted invite that was originally sent to email
        accepted_invite = OrganisationMemberFactory(
            user=user,  # User is now linked after accepting
            invite_email=user.email,
            organisation=organisation,
            accepted_datetime=timezone.now(),
        )

        request = rf.get("/fake-url/")
        request.user = user
        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK
        accepted_organisations = list(
            response.context_data["organisation_table"].data,
        )
        assert len(accepted_organisations) == 1
        assert accepted_organisations[0].uuid == accepted_invite.uuid
        assert response.context_data["has_organisations"] is True
