from decimal import Decimal
from http import HTTPStatus
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from ams.memberships.tests.factories import MembershipOptionFactory
from ams.memberships.tests.factories import OrganisationMembershipFactory
from ams.organisations.models import OrganisationMember
from ams.organisations.tests.factories import OrganisationFactory
from ams.organisations.tests.factories import OrganisationMemberFactory
from ams.users.models import User
from ams.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
class TestAddOrganisationSeatsView:
    def test_access_requires_login(self, client):
        org = OrganisationFactory()
        url = reverse("memberships:add_seats", kwargs={"uuid": org.uuid})
        response = client.get(url)
        assert response.status_code == HTTPStatus.FOUND
        assert "/accounts/login/" in response.url

    def test_access_requires_org_admin(self, user: User, client):
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.MEMBER,
            accepted_datetime=timezone.now(),
        )
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
        )
        OrganisationMembershipFactory(
            organisation=org,
            membership_option=membership_option,
            start_date=timezone.localdate(),
            approved=True,
        )
        client.force_login(user)
        url = reverse("memberships:add_seats", kwargs={"uuid": org.uuid})
        response = client.get(url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_staff_can_access(self, client):
        staff_user = UserFactory(is_staff=True)
        org = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
        )
        OrganisationMembershipFactory(
            organisation=org,
            membership_option=membership_option,
            start_date=timezone.localdate(),
            approved=True,
        )
        client.force_login(staff_user)
        url = reverse("memberships:add_seats", kwargs={"uuid": org.uuid})
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_get_no_active_membership_redirects(self, user: User, client):
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        client.force_login(user)
        url = reverse("memberships:add_seats", kwargs={"uuid": org.uuid})
        response = client.get(url)
        assert response.status_code == HTTPStatus.FOUND

    def test_get_with_active_membership_displays_form(self, user: User, client):
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
        )
        membership = OrganisationMembershipFactory(
            organisation=org,
            membership_option=membership_option,
            start_date=timezone.localdate(),
            approved=True,
            seats=10,
        )
        client.force_login(user)
        url = reverse("memberships:add_seats", kwargs={"uuid": org.uuid})
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert "form" in response.context
        assert response.context["organisation"] == org
        assert response.context["active_membership"] == membership

    @patch("ams.memberships.forms.get_billing_service")
    def test_post_valid_adds_seats(self, mock_get_billing_service, user: User, client):
        mock_get_billing_service.return_value = None
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("0.00"),
            duration={"years": 1},
            max_seats=None,  # Unlimited seats to allow adding
        )
        membership = OrganisationMembershipFactory(
            organisation=org,
            membership_option=membership_option,
            start_date=timezone.localdate(),
            approved=True,
            seats=10,
        )
        client.force_login(user)
        url = reverse("memberships:add_seats", kwargs={"uuid": org.uuid})
        data = {"seats_to_add": 5}
        response = client.post(url, data=data)
        assert response.status_code == HTTPStatus.FOUND
        membership.refresh_from_db()
        assert membership.seats == Decimal("15")

    @patch("ams.memberships.forms.get_billing_service")
    def test_post_valid_creates_invoice(
        self,
        mock_get_billing_service,
        user: User,
        client,
    ):
        mock_billing_service = Mock()
        mock_invoice = Mock()
        mock_invoice.invoice_number = "INV-12345"
        mock_billing_service.create_invoice.return_value = mock_invoice
        mock_get_billing_service.return_value = mock_billing_service
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
            max_seats=None,  # Unlimited seats to allow adding
        )
        OrganisationMembershipFactory(
            organisation=org,
            membership_option=membership_option,
            start_date=timezone.localdate(),
            approved=True,
            seats=10,
        )
        client.force_login(user)
        url = reverse("memberships:add_seats", kwargs={"uuid": org.uuid})
        data = {"seats_to_add": 5}
        response = client.post(url, data=data)
        assert response.status_code == HTTPStatus.FOUND
        assert mock_billing_service.create_invoice.called

    @patch("ams.memberships.forms.get_billing_service")
    @patch("ams.memberships.views.send_staff_organisation_seats_added_notification")
    def test_post_valid_sends_notification(
        self,
        mock_send_notification,
        mock_get_billing_service,
        user: User,
        client,
    ):
        mock_get_billing_service.return_value = None
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("0.00"),
            duration={"years": 1},
            max_seats=None,  # Unlimited seats to allow adding
        )
        OrganisationMembershipFactory(
            organisation=org,
            membership_option=membership_option,
            start_date=timezone.localdate(),
            approved=True,
            seats=10,
        )
        client.force_login(user)
        url = reverse("memberships:add_seats", kwargs={"uuid": org.uuid})
        data = {"seats_to_add": 5}
        response = client.post(url, data=data)
        assert response.status_code == HTTPStatus.FOUND
        assert mock_send_notification.called

    def test_post_invalid_shows_errors(self, user: User, client):
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
        )
        OrganisationMembershipFactory(
            organisation=org,
            membership_option=membership_option,
            start_date=timezone.localdate(),
            approved=True,
        )
        client.force_login(user)
        url = reverse("memberships:add_seats", kwargs={"uuid": org.uuid})
        data = {"seats_to_add": 0}
        response = client.post(url, data=data)
        assert response.status_code == HTTPStatus.OK
        assert "form" in response.context
        assert response.context["form"].errors

    def test_context_includes_seat_info(self, user: User, client):
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
            max_seats=None,  # Unlimited seats
        )
        membership = OrganisationMembershipFactory(
            organisation=org,
            membership_option=membership_option,
            start_date=timezone.localdate(),
            approved=True,
            seats=10,
        )
        client.force_login(user)
        url = reverse("memberships:add_seats", kwargs={"uuid": org.uuid})
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert "current_seats" in response.context
        assert response.context["current_seats"] == membership.seats
        assert "occupied_seats" in response.context
        assert response.context["occupied_seats"] == membership.occupied_seats
        assert "prorata_cost_per_seat" in response.context
