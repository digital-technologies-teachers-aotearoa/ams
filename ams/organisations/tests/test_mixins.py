"""Tests for user mixins."""

from http import HTTPStatus

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
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

    def test_superuser_returns_true_without_cache(self):
        """Test that superusers return True and bypass cache."""
        org = OrganisationFactory()
        user = UserFactory(is_superuser=True)

        # Clear cache to ensure we're not relying on it
        cache.clear()

        # Superuser should return True without needing DB query or cache
        assert user_is_organisation_admin(user, org) is True

        # Verify no cache was set for superuser
        cache_key = f"user_is_org_admin_{user.id}_{org.id}"
        assert cache.get(cache_key) is None

    def test_caches_result_for_admin(self):
        """Test that admin check result is cached."""
        org = OrganisationFactory()
        user = UserFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        cache.clear()

        # First call should query DB and cache result
        cache_key = f"user_is_org_admin_{user.id}_{org.id}"
        assert cache.get(cache_key) is None

        result = user_is_organisation_admin(user, org)

        assert result is True
        assert cache.get(cache_key) is True

    def test_caches_result_for_non_admin(self):
        """Test that non-admin check result is also cached."""
        org = OrganisationFactory()
        user = UserFactory()

        cache.clear()

        # First call should query DB and cache result
        cache_key = f"user_is_org_admin_{user.id}_{org.id}"
        assert cache.get(cache_key) is None

        result = user_is_organisation_admin(user, org)

        assert result is False
        assert cache.get(cache_key) is False

    def test_uses_cached_result_on_second_call(self):
        """Test that second call uses cached result."""
        org = OrganisationFactory()
        user = UserFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        cache.clear()
        cache_key = f"user_is_org_admin_{user.id}_{org.id}"

        # First call
        result1 = user_is_organisation_admin(user, org)
        assert result1 is True

        # Manually set cache to False to verify second call uses cache
        cache.set(cache_key, False, 300)  # noqa: FBT003

        # Second call should return cached False (not DB True)
        result2 = user_is_organisation_admin(user, org)
        assert result2 is False

    def test_cache_invalidated_on_member_role_change(self):
        """Test cache is cleared when member role changes."""
        org = OrganisationFactory()
        user = UserFactory()
        member = OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        )

        cache.clear()
        cache_key = f"user_is_org_admin_{user.id}_{org.id}"

        # First call - should be False and cached
        result1 = user_is_organisation_admin(user, org)
        assert result1 is False
        assert cache.get(cache_key) is False

        # Change role to ADMIN (should trigger cache invalidation via signal)
        member.role = OrganisationMember.Role.ADMIN
        member.save()

        # Cache should be cleared
        assert cache.get(cache_key) is None

        # Next call should query DB and get new result
        result2 = user_is_organisation_admin(user, org)
        assert result2 is True

    def test_cache_invalidated_on_member_delete(self):
        """Test cache is cleared when member is deleted."""
        org = OrganisationFactory()
        user = UserFactory()
        member = OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        cache.clear()
        cache_key = f"user_is_org_admin_{user.id}_{org.id}"

        # First call - should be True and cached
        result1 = user_is_organisation_admin(user, org)
        assert result1 is True
        assert cache.get(cache_key) is True

        # Delete member (should trigger cache invalidation via signal)
        member.delete()

        # Cache should be cleared
        assert cache.get(cache_key) is None


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
