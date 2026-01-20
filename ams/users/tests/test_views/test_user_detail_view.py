from http import HTTPStatus

import pytest
from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from ams.organisations.tests.factories import OrganisationFactory
from ams.organisations.tests.factories import OrganisationMemberFactory
from ams.users.models import ProfileField
from ams.users.models import ProfileFieldGroup
from ams.users.models import ProfileFieldResponse
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

    def test_shows_pending_invites_sent_to_secondary_email(
        self,
        user: User,
        rf: RequestFactory,
    ):
        """Test that pending invites sent to user's secondary email are shown."""
        # Add a secondary verified email to the user
        secondary_email = "secondary@example.com"
        EmailAddress.objects.create(
            user=user,
            email=secondary_email,
            verified=True,
            primary=False,
        )

        organisation = OrganisationFactory()

        # Create an invite to the secondary email
        invite = OrganisationMemberFactory(
            invite=True,  # Sets user=None
            invite_email=secondary_email,
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
        assert response.context_data["has_pending_invitations"] is True

    def test_does_not_show_invites_to_unverified_secondary_email(
        self,
        user: User,
        rf: RequestFactory,
    ):
        """Test that invites to unverified secondary emails are NOT shown."""
        # Add an UNVERIFIED secondary email
        unverified_email = "unverified@example.com"
        EmailAddress.objects.create(
            user=user,
            email=unverified_email,
            verified=False,  # Not verified
            primary=False,
        )

        organisation = OrganisationFactory()

        # Create an invite to the unverified email
        OrganisationMemberFactory(
            invite=True,
            invite_email=unverified_email,
            organisation=organisation,
        )

        request = rf.get("/fake-url/")
        request.user = user
        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK
        # Should NOT see the invite
        assert response.context_data["has_pending_invitations"] is False

    def test_profile_completion_context_no_fields(self, user: User, rf: RequestFactory):
        """Test profile completion context when no profile fields exist."""
        request = rf.get("/fake-url/")
        request.user = user
        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK
        assert response.context_data["profile_completion_percentage"] == 100  # noqa: PLR2004
        assert response.context_data["profile_incomplete_count"] == 0

    def test_profile_completion_context_with_incomplete_profile(
        self,
        user: User,
        rf: RequestFactory,
    ):
        """Test profile completion context when profile is incomplete."""
        # Create profile fields
        group = ProfileFieldGroup.objects.create(
            name_translations={"en": "Test Group"},
            order=1,
            is_active=True,
        )
        field1 = ProfileField.objects.create(
            field_key="field1",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Field 1"},
            group=group,
            is_active=True,
        )
        ProfileField.objects.create(
            field_key="field2",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Field 2"},
            group=group,
            is_active=True,
        )

        # User has filled only one of two fields
        ProfileFieldResponse.objects.create(
            user=user,
            profile_field=field1,
            value="Test",
        )

        request = rf.get("/fake-url/")
        request.user = user
        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK
        assert response.context_data["profile_completion_percentage"] == 50  # noqa: PLR2004
        assert response.context_data["profile_incomplete_count"] == 1

    def test_profile_completion_context_with_complete_profile(
        self,
        user: User,
        rf: RequestFactory,
    ):
        """Test profile completion context when profile is complete."""
        # Create profile fields
        group = ProfileFieldGroup.objects.create(
            name_translations={"en": "Test Group"},
            order=1,
            is_active=True,
        )
        field1 = ProfileField.objects.create(
            field_key="field1",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Field 1"},
            group=group,
            is_active=True,
        )
        field2 = ProfileField.objects.create(
            field_key="field2",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Field 2"},
            group=group,
            is_active=True,
        )

        # User has filled all fields
        ProfileFieldResponse.objects.create(
            user=user,
            profile_field=field1,
            value="Test 1",
        )
        ProfileFieldResponse.objects.create(
            user=user,
            profile_field=field2,
            value="Test 2",
        )

        request = rf.get("/fake-url/")
        request.user = user
        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK
        assert response.context_data["profile_completion_percentage"] == 100  # noqa: PLR2004
        assert response.context_data["profile_incomplete_count"] == 0

    def test_profile_completion_ignores_inactive_fields(
        self,
        user: User,
        rf: RequestFactory,
    ):
        """Test profile completion only counts active fields."""
        # Create profile fields
        group = ProfileFieldGroup.objects.create(
            name_translations={"en": "Test Group"},
            order=1,
            is_active=True,
        )
        active_field = ProfileField.objects.create(
            field_key="active",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Active Field"},
            group=group,
            is_active=True,
        )
        ProfileField.objects.create(
            field_key="inactive",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Inactive Field"},
            group=group,
            is_active=False,
        )

        # User has filled the active field only
        ProfileFieldResponse.objects.create(
            user=user,
            profile_field=active_field,
            value="Test",
        )

        request = rf.get("/fake-url/")
        request.user = user
        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK
        # Should be 100% complete (1/1 active fields filled)
        assert response.context_data["profile_completion_percentage"] == 100  # noqa: PLR2004
        assert response.context_data["profile_incomplete_count"] == 0

    def test_profile_completion_excludes_non_counting_fields(
        self,
        user: User,
        rf: RequestFactory,
    ):
        """Test profile completion excludes fields not counting toward completion."""
        # Create profile fields
        group = ProfileFieldGroup.objects.create(
            name_translations={"en": "Test Group"},
            order=1,
            is_active=True,
        )
        counting_field = ProfileField.objects.create(
            field_key="counting",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Counting Field"},
            group=group,
            is_active=True,
            counts_toward_completion=True,
        )
        non_counting_field = ProfileField.objects.create(
            field_key="non_counting",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Non-Counting Field"},
            group=group,
            is_active=True,
            counts_toward_completion=False,
        )

        # User has filled both fields
        ProfileFieldResponse.objects.create(
            user=user,
            profile_field=counting_field,
            value="Test 1",
        )
        ProfileFieldResponse.objects.create(
            user=user,
            profile_field=non_counting_field,
            value="Test 2",
        )

        request = rf.get("/fake-url/")
        request.user = user
        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK
        # Should be 100% complete (1/1 counting fields filled)
        assert response.context_data["profile_completion_percentage"] == 100  # noqa: PLR2004
        assert response.context_data["profile_incomplete_count"] == 0

    def test_profile_completion_incomplete_with_non_counting_fields(
        self,
        user: User,
        rf: RequestFactory,
    ):
        """Test profile completion when only non-counting fields are filled."""
        # Create profile fields
        group = ProfileFieldGroup.objects.create(
            name_translations={"en": "Test Group"},
            order=1,
            is_active=True,
        )
        ProfileField.objects.create(
            field_key="counting1",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Counting Field 1"},
            group=group,
            is_active=True,
            counts_toward_completion=True,
        )
        ProfileField.objects.create(
            field_key="counting2",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Counting Field 2"},
            group=group,
            is_active=True,
            counts_toward_completion=True,
        )
        non_counting_field = ProfileField.objects.create(
            field_key="non_counting",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Non-Counting Field"},
            group=group,
            is_active=True,
            counts_toward_completion=False,
        )

        # User has filled only the non-counting field
        ProfileFieldResponse.objects.create(
            user=user,
            profile_field=non_counting_field,
            value="Test",
        )

        request = rf.get("/fake-url/")
        request.user = user
        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK
        # Should be 0% complete (0/2 counting fields filled)
        assert response.context_data["profile_completion_percentage"] == 0
        assert response.context_data["profile_incomplete_count"] == 2  # noqa: PLR2004

    def test_profile_completion_mixed_counting_fields(
        self,
        user: User,
        rf: RequestFactory,
    ):
        """Test profile completion with mixed counting and non-counting fields."""
        # Create profile fields
        group = ProfileFieldGroup.objects.create(
            name_translations={"en": "Test Group"},
            order=1,
            is_active=True,
        )
        counting_field1 = ProfileField.objects.create(
            field_key="counting1",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Counting Field 1"},
            group=group,
            is_active=True,
            counts_toward_completion=True,
        )
        counting_field2 = ProfileField.objects.create(
            field_key="counting2",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Counting Field 2"},
            group=group,
            is_active=True,
            counts_toward_completion=True,
        )
        ProfileField.objects.create(
            field_key="counting3",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Counting Field 3"},
            group=group,
            is_active=True,
            counts_toward_completion=True,
        )
        non_counting_field1 = ProfileField.objects.create(
            field_key="non_counting1",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Non-Counting Field 1"},
            group=group,
            is_active=True,
            counts_toward_completion=False,
        )
        ProfileField.objects.create(
            field_key="non_counting2",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Non-Counting Field 2"},
            group=group,
            is_active=True,
            counts_toward_completion=False,
        )

        # User has filled 2 counting fields and 1 non-counting field
        ProfileFieldResponse.objects.create(
            user=user,
            profile_field=counting_field1,
            value="Test 1",
        )
        ProfileFieldResponse.objects.create(
            user=user,
            profile_field=counting_field2,
            value="Test 2",
        )
        ProfileFieldResponse.objects.create(
            user=user,
            profile_field=non_counting_field1,
            value="Test 3",
        )

        request = rf.get("/fake-url/")
        request.user = user
        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK
        # Should be 66% complete (2/3 counting fields filled)
        assert response.context_data["profile_completion_percentage"] == 66  # noqa: PLR2004
        assert response.context_data["profile_incomplete_count"] == 1
