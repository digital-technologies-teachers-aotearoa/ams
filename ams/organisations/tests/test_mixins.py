"""Tests for user mixins."""

from http import HTTPStatus

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from django.utils import timezone
from django.views.generic import DetailView

from ams.organisations.mixins import OrganisationAdminMixin
from ams.organisations.mixins import user_is_organisation_admin
from ams.organisations.models import Organisation
from ams.organisations.models import OrganisationMember
from ams.organisations.tests.factories import OrganisationFactory
from ams.organisations.tests.factories import OrganisationMemberFactory
from ams.users.tests.factories import UserFactory


@pytest.mark.django_db
class TestUserIsOrganisationAdmin:
    """Tests for user_is_organisation_admin helper function."""

    def test_unauthenticated_user_returns_false(self):
        """Test that unauthenticated users are not admins."""
        org = OrganisationFactory()
        user = AnonymousUser()

        assert user_is_organisation_admin(user, org) is False

    def test_admin_member_returns_true(self):
        """Test that admin members return True."""
        org = OrganisationFactory()
        user = UserFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        assert user_is_organisation_admin(user, org) is True

    def test_regular_member_returns_false(self):
        """Test that regular members return False."""
        org = OrganisationFactory()
        user = UserFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        )

        assert user_is_organisation_admin(user, org) is False

    def test_non_member_returns_false(self):
        """Test that non-members return False."""
        org = OrganisationFactory()
        user = UserFactory()

        assert user_is_organisation_admin(user, org) is False

    def test_admin_of_different_org_returns_false(self):
        """Test that admins of other organisations return False."""
        org1 = OrganisationFactory()
        org2 = OrganisationFactory()
        user = UserFactory()
        OrganisationMemberFactory(
            organisation=org1,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        assert user_is_organisation_admin(user, org2) is False


@pytest.mark.django_db
class TestOrganisationAdminMixin:
    """Tests for OrganisationAdminMixin."""

    class _TestView(OrganisationAdminMixin, DetailView):
        """Test view using the mixin."""

        model = Organisation
        pk_url_kwarg = "uuid"

        def get_object(self, queryset=None):
            """Get organisation by UUID."""
            uuid = self.kwargs.get(self.pk_url_kwarg)
            return Organisation.objects.get(uuid=uuid)

    def test_staff_user_has_access(self, rf: RequestFactory):
        """Test that staff users can access any organisation."""
        org = OrganisationFactory()
        user = UserFactory(is_staff=True)

        request = rf.get(f"/organisations/{org.uuid}/")
        request.user = user

        view = self._TestView.as_view()
        response = view(request, uuid=org.uuid)

        assert response.status_code == HTTPStatus.OK

    def test_superuser_has_access(self, rf: RequestFactory):
        """Test that superusers can access any organisation."""
        org = OrganisationFactory()
        user = UserFactory(is_superuser=True)

        request = rf.get(f"/organisations/{org.uuid}/")
        request.user = user

        view = self._TestView.as_view()
        response = view(request, uuid=org.uuid)

        assert response.status_code == HTTPStatus.OK

    def test_org_admin_has_access(self, rf: RequestFactory):
        """Test that organisation admins can access their organisation."""
        org = OrganisationFactory()
        user = UserFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        request = rf.get(f"/organisations/{org.uuid}/")
        request.user = user

        view = self._TestView.as_view()
        response = view(request, uuid=org.uuid)

        assert response.status_code == HTTPStatus.OK

    def test_regular_member_denied_access(self, rf: RequestFactory):
        """Test that regular members are denied access."""
        org = OrganisationFactory()
        user = UserFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        )

        request = rf.get(f"/organisations/{org.uuid}/")
        request.user = user

        view = self._TestView.as_view()

        with pytest.raises(PermissionDenied):
            view(request, uuid=org.uuid)

    def test_non_member_denied_access(self, rf: RequestFactory):
        """Test that non-members are denied access."""
        org = OrganisationFactory()
        user = UserFactory()

        request = rf.get(f"/organisations/{org.uuid}/")
        request.user = user

        view = self._TestView.as_view()

        with pytest.raises(PermissionDenied):
            view(request, uuid=org.uuid)

    def test_admin_of_different_org_denied_access(self, rf: RequestFactory):
        """Test that admins of other organisations are denied access."""
        org1 = OrganisationFactory()
        org2 = OrganisationFactory()
        user = UserFactory()
        OrganisationMemberFactory(
            organisation=org1,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        request = rf.get(f"/organisations/{org2.uuid}/")
        request.user = user

        view = self._TestView.as_view()

        with pytest.raises(PermissionDenied):
            view(request, uuid=org2.uuid)
