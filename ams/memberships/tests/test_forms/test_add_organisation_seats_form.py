from decimal import Decimal
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from dateutil.relativedelta import relativedelta
from django.utils import timezone

from ams.memberships.forms import AddOrganisationSeatsForm
from ams.memberships.tests.factories import MembershipOptionFactory
from ams.memberships.tests.factories import OrganisationMembershipFactory
from ams.organisations.tests.factories import OrganisationFactory


@pytest.mark.django_db
class TestAddOrganisationSeatsForm:
    """Tests for the AddOrganisationSeatsForm."""

    def test_form_valid_with_active_membership(self):
        """Test form is valid with valid data and active membership."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
            max_seats=None,  # Unlimited seats to allow adding
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=timezone.localdate(),
            approved=True,
            seats=10,
        )

        form = AddOrganisationSeatsForm(
            organisation=organisation,
            active_membership=membership,
            data={"seats_to_add": 5},
        )

        assert form.is_valid(), form.errors
        expected_seats = 5
        assert form.cleaned_data["seats_to_add"] == expected_seats

    def test_form_invalid_zero_seats(self):
        """Test form validation rejects zero seats."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            approved=True,
        )

        form = AddOrganisationSeatsForm(
            organisation=organisation,
            active_membership=membership,
            data={"seats_to_add": 0},
        )

        assert not form.is_valid()
        assert "seats_to_add" in form.errors
        assert form.errors["seats_to_add"][0].startswith(
            "Ensure this value is greater than",
        )

    def test_form_invalid_negative_seats(self):
        """Test form validation rejects negative seats."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            approved=True,
        )

        form = AddOrganisationSeatsForm(
            organisation=organisation,
            active_membership=membership,
            data={"seats_to_add": -5},
        )

        assert not form.is_valid()
        assert "seats_to_add" in form.errors

    def test_calculate_prorata_delegates_to_service(self):
        """Test that form method correctly delegates to service function."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=timezone.localdate(),
            approved=True,
        )

        form = AddOrganisationSeatsForm(
            organisation=organisation,
            active_membership=membership,
        )

        with patch("ams.memberships.forms.calculate_prorata_seat_cost") as mock_service:
            mock_service.return_value = Decimal("500.00")

            result = form.calculate_prorata_cost(5)

            # Verify service function was called with correct arguments
            mock_service.assert_called_once_with(membership, 5)
            assert result == Decimal("500.00")

    @patch("ams.memberships.forms.get_billing_service")
    def test_form_saves_updates_max_seats(self, mock_get_billing_service):
        """Test save() method updates seats on membership."""
        # Mock billing service to return None (no billing configured)
        mock_get_billing_service.return_value = None

        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("0.00"),  # Free membership, no invoice needed
            duration={"years": 1},
            max_seats=None,  # Unlimited seats to allow adding
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=timezone.localdate(),
            approved=True,
            seats=10,
        )

        initial_seats = membership.seats

        form = AddOrganisationSeatsForm(
            organisation=organisation,
            active_membership=membership,
            data={"seats_to_add": 5},
        )

        assert form.is_valid()
        saved_membership, _invoice = form.save()

        # Refresh from database
        membership.refresh_from_db()

        assert membership.seats == initial_seats + Decimal("5")
        assert saved_membership.pk == membership.pk

    @patch("ams.memberships.forms.get_billing_service")
    def test_form_saves_creates_invoice(self, mock_get_billing_service):
        """Test save() method creates invoice when billing is configured."""
        # Mock billing service
        mock_billing_service = Mock()
        mock_invoice = Mock()
        mock_invoice.invoice_number = "INV-12345"
        mock_billing_service.create_invoice.return_value = mock_invoice
        mock_get_billing_service.return_value = mock_billing_service

        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
            max_seats=None,  # Unlimited seats to allow adding
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=timezone.localdate(),
            approved=True,
            seats=10,
        )

        form = AddOrganisationSeatsForm(
            organisation=organisation,
            active_membership=membership,
            data={"seats_to_add": 5},
        )

        assert form.is_valid()
        _saved_membership, invoice = form.save()

        # Verify billing service was called
        assert mock_billing_service.create_invoice.called
        assert invoice == mock_invoice

        # Verify invoice line items
        call_args = mock_billing_service.create_invoice.call_args
        line_items = call_args[0][3]  # 4th positional argument

        expected_quantity = 5
        assert len(line_items) == 1
        assert line_items[0]["quantity"] == expected_quantity
        assert "description" in line_items[0]
        assert "unit_amount" in line_items[0]

    def test_form_rejects_membership_expiring_today(self):
        """Test form validation rejects membership expiring today."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
        )

        # Membership expires today
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=timezone.localdate() - relativedelta(years=1),
            expiry_date=timezone.localdate(),
            approved=True,
        )

        form = AddOrganisationSeatsForm(
            organisation=organisation,
            active_membership=membership,
            data={"seats_to_add": 5},
        )

        assert not form.is_valid()
        assert "seats_to_add" in form.errors
        assert "expires too soon" in form.errors["seats_to_add"][0]
