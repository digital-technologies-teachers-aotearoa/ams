from http import HTTPStatus

import pytest
from django.urls import reverse
from django.utils import timezone

from ams.users.models import OrganisationMember
from ams.users.models import User
from ams.users.tests.factories import OrganisationFactory
from ams.users.tests.factories import OrganisationMemberFactory
from ams.users.tests.factories import UserFactory
from ams.users.views import OrganisationUpdateView

pytestmark = pytest.mark.django_db


class TestOrganisationUpdateView:
    """Tests for the OrganisationUpdateView"""

    def test_update_organisation_as_org_admin(self, user: User, client):
        """Test that organisation admins can update their organisation."""
        client.force_login(user)

        # Create organisation with user as admin
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        url = reverse("users:organisation_update", kwargs={"uuid": org.uuid})

        data = {
            "name": "Updated Organisation",
            "telephone": org.telephone,
            "email": org.email,
            "contact_name": org.contact_name,
            "postal_address": org.postal_address,
            "postal_city": org.postal_city,
            "postal_code": org.postal_code,
        }

        response = client.post(url, data=data)

        # Should redirect to home
        assert response.status_code == HTTPStatus.FOUND

        # Organisation should be updated
        org.refresh_from_db()
        assert org.name == "Updated Organisation"

    def test_update_organisation_as_staff(self, user: User, client):
        """Test that staff can update any organisation."""
        user.is_staff = True
        user.save()
        client.force_login(user)

        org = OrganisationFactory()

        url = reverse("users:organisation_update", kwargs={"uuid": org.uuid})

        data = {
            "name": "Updated by Staff",
            "telephone": org.telephone,
            "email": org.email,
            "contact_name": org.contact_name,
            "postal_address": org.postal_address,
            "postal_city": org.postal_city,
            "postal_code": org.postal_code,
        }

        response = client.post(url, data=data)

        # Should redirect to home
        assert response.status_code == HTTPStatus.FOUND

        # Organisation should be updated
        org.refresh_from_db()
        assert org.name == "Updated by Staff"

    def test_update_organisation_no_permission(self, client):
        """Test that users without permission cannot update organisations."""
        user = UserFactory()
        client.force_login(user)

        org = OrganisationFactory()

        url = reverse("users:organisation_update", kwargs={"uuid": org.uuid})

        data = {
            "name": "Unauthorized Update",
            "telephone": org.telephone,
            "email": org.email,
            "contact_name": org.contact_name,
            "postal_address": org.postal_address,
            "postal_city": org.postal_city,
            "postal_code": org.postal_code,
        }

        response = client.post(url, data=data)

        # Should return 403 Forbidden
        assert response.status_code == HTTPStatus.FORBIDDEN

        # Organisation should NOT be updated
        org.refresh_from_db()
        assert org.name != "Unauthorized Update"

    def test_update_organisation_has_cancel_url(self, user: User, client):
        """Test that OrganisationUpdateView provides cancel_url to the form."""
        client.force_login(user)

        # Create organisation with user as admin
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        url = reverse("users:organisation_update", kwargs={"uuid": org.uuid})

        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        # Check that the cancel link is present in the rendered form
        expected_cancel_url = reverse(
            "users:detail",
            kwargs={"username": user.username},
        )
        assert expected_cancel_url in response.content.decode()
        # Check for the Cancel button
        assert "Cancel" in response.content.decode()

    def test_update_organisation_cancel_url_in_form_kwargs(self, user: User, rf):
        """Test that cancel_url is passed to form kwargs in OrganisationUpdateView."""
        # Create organisation with user as admin
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )

        request = rf.get("/fake-url/")
        request.user = user

        view = OrganisationUpdateView()
        view.request = request
        view.kwargs = {"uuid": org.uuid}

        form_kwargs = view.get_form_kwargs()

        expected_cancel_url = reverse(
            "users:organisation_detail",
            kwargs={"uuid": org.uuid},
        )
        assert "cancel_url" in form_kwargs
        assert form_kwargs["cancel_url"] == expected_cancel_url
