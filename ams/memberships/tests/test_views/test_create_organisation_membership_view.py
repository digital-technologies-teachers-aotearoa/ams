from http import HTTPStatus

import pytest
from django.urls import reverse
from django.utils import timezone

from ams.memberships.models import MembershipOptionType
from ams.memberships.models import OrganisationMembership
from ams.memberships.tests.factories import MembershipOptionFactory
from ams.organisations.models import OrganisationMember
from ams.organisations.tests.factories import OrganisationFactory
from ams.organisations.tests.factories import OrganisationMemberFactory
from ams.users.models import User

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
class TestCreateOrganisationMembershipView:
    """Tests for the CreateOrganisationMembershipView."""

    def test_add_membership_as_org_admin(self, user: User, client):
        """Test that organisation admins can add memberships."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            max_seats=10,
            cost=0,  # Use zero cost to avoid billing setup
        )

        client.force_login(user)
        url = reverse("memberships:apply-organisation", kwargs={"uuid": org.uuid})
        data = {
            "membership_option": option.id,
            "start_date": timezone.localdate(),
            "seat_count": 5,
        }

        response = client.post(url, data=data)

        # Should redirect to organisation detail
        assert response.status_code == HTTPStatus.FOUND
        assert f"/organisations/{org.uuid}/" in response.url

        # Membership should be created
        membership = OrganisationMembership.objects.get(organisation=org)
        assert membership.membership_option == option
        assert membership.max_seats == 5  # noqa: PLR2004
        assert membership.start_date == timezone.localdate()

    def test_add_membership_as_staff(self, admin_user: User, client):
        """Test that staff/admin users can add memberships."""
        org = OrganisationFactory()
        option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            max_seats=10,
            cost=0,  # Use zero cost to avoid billing setup
        )

        client.force_login(admin_user)
        url = reverse("memberships:apply-organisation", kwargs={"uuid": org.uuid})
        data = {
            "membership_option": option.id,
            "start_date": timezone.localdate(),
            "seat_count": 5,
        }

        response = client.post(url, data=data)

        # Should redirect to organisation detail
        assert response.status_code == HTTPStatus.FOUND
        assert f"/organisations/{org.uuid}/" in response.url

        # Membership should be created
        membership = OrganisationMembership.objects.get(organisation=org)
        assert membership.membership_option == option
        assert membership.max_seats == 5  # noqa: PLR2004

    def test_add_membership_not_org_admin(self, user: User, client):
        """Test that non-admin members cannot add memberships."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.MEMBER,  # Not admin
            accepted_datetime=timezone.now(),
        )
        MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            max_seats=10,
        )

        client.force_login(user)
        url = reverse("memberships:apply-organisation", kwargs={"uuid": org.uuid})

        response = client.get(url)

        # Should be forbidden
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_add_membership_not_authenticated(self, client):
        """Test that unauthenticated users cannot add memberships."""
        org = OrganisationFactory()
        url = reverse("memberships:apply-organisation", kwargs={"uuid": org.uuid})

        response = client.get(url)

        # Should redirect to login
        assert response.status_code == HTTPStatus.FOUND
        assert "/accounts/login/" in response.url

    def test_add_membership_form_displays_correctly(self, user: User, client):
        """Test that the form displays with correct context."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            max_seats=10,
            cost=100,
        )

        client.force_login(user)
        url = reverse("memberships:apply-organisation", kwargs={"uuid": org.uuid})

        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert "organisation" in response.context
        assert response.context["organisation"] == org
        assert "form" in response.context
        assert "membership_data_json" in response.context
        # Verify the membership data contains the option we created
        membership_data = response.context["membership_data_json"]
        assert str(option.id) in membership_data
        assert membership_data[str(option.id)]["cost"] == 100.0  # noqa: PLR2004
        assert membership_data[str(option.id)]["max_seats"] == 10  # noqa: PLR2004

    def test_add_membership_invalid_seat_count(self, user: User, client):
        """Test that invalid seat count shows form errors."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            max_seats=10,
        )

        client.force_login(user)
        url = reverse("memberships:apply-organisation", kwargs={"uuid": org.uuid})
        data = {
            "membership_option": option.id,
            "start_date": timezone.localdate(),
            "seat_count": 15,  # Exceeds max
        }

        response = client.post(url, data=data)

        # Should not redirect (form invalid)
        assert response.status_code == HTTPStatus.OK
        assert "cannot exceed the maximum seats" in response.content.decode()

        # Should not create membership
        assert not OrganisationMembership.objects.filter(organisation=org).exists()

    def test_add_membership_success_message(self, user: User, client):
        """Test that success message is shown after adding membership."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            max_seats=10,
            cost=0,  # Use zero cost to avoid billing setup
        )

        client.force_login(user)
        url = reverse("memberships:apply-organisation", kwargs={"uuid": org.uuid})
        data = {
            "membership_option": option.id,
            "start_date": timezone.localdate(),
            "seat_count": 5,
        }

        response = client.post(url, data=data, follow=True)

        # Check success message
        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "Membership added successfully" in str(messages[0])
        assert "5 seats" in str(messages[0])

    def test_add_membership_with_zero_cost_no_invoice(self, user: User, client):
        """Test that zero-cost memberships don't create invoices."""
        org = OrganisationFactory()
        OrganisationMemberFactory(
            organisation=org,
            user=user,
            role=OrganisationMember.Role.ADMIN,
            accepted_datetime=timezone.now(),
        )
        option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            max_seats=10,
            cost=0,  # Free
        )

        client.force_login(user)
        url = reverse("memberships:apply-organisation", kwargs={"uuid": org.uuid})
        data = {
            "membership_option": option.id,
            "start_date": timezone.localdate(),
            "seat_count": 5,
        }

        response = client.post(url, data=data)

        assert response.status_code == HTTPStatus.FOUND

        # Membership should be created without invoice
        membership = OrganisationMembership.objects.get(organisation=org)
        assert membership.invoice is None
