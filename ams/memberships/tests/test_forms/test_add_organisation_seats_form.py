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

    @patch("ams.memberships.forms.MembershipBillingService")
    def test_form_saves_updates_max_seats(self, mock_billing_service_class):
        """Test save() method updates seats on membership."""
        # Mock billing service to return None for invoice (free membership)
        mock_billing_service = Mock()
        mock_billing_service.create_membership_invoice.return_value = None
        mock_billing_service_class.return_value = mock_billing_service

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

    @patch("ams.memberships.forms.MembershipBillingService")
    def test_form_saves_creates_invoice(self, mock_billing_service_class):
        """Test save() method creates invoice when billing is configured."""
        # Mock billing service and invoice
        mock_billing_service = Mock()
        mock_invoice = Mock()
        mock_invoice.invoice_number = "INV-12345"
        mock_billing_service.create_membership_invoice.return_value = mock_invoice
        mock_billing_service_class.return_value = mock_billing_service

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

        # Verify billing service method was called
        assert mock_billing_service.create_membership_invoice.called
        assert invoice == mock_invoice

        # Verify create_membership_invoice was called with correct arguments
        call_args = mock_billing_service.create_membership_invoice.call_args
        expected_quantity = 5
        assert call_args[1]["seat_count"] == expected_quantity
        assert call_args[1]["membership"] == membership
        assert "unit_price_override" in call_args[1]
        # Unit price should be prorata_cost / seats_to_add
        assert call_args[1]["unit_price_override"] is not None

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

    @patch("ams.memberships.forms.MembershipBillingService")
    def test_add_seats_respects_max_charged_seats(self, mock_billing_service_class):
        """Test adding seats when max_charged_seats limits billing."""
        # Arrange
        mock_billing_service = Mock()
        mock_billing_service.create_membership_invoice.return_value = None
        mock_billing_service_class.return_value = mock_billing_service

        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
            max_charged_seats=4,
        )
        start_date = timezone.localdate()
        expiry_date = start_date + relativedelta(years=1)
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
            seats=2,  # Currently have 2 seats
            approved=True,
        )

        form = AddOrganisationSeatsForm(
            organisation=organisation,
            active_membership=membership,
            data={"seats_to_add": 5},  # Adding 5 more (total will be 7)
        )

        # Act
        assert form.is_valid(), form.errors
        updated_membership, _invoice = form.save()

        # Assert
        # Membership should have 7 seats total
        updated_membership.refresh_from_db()
        expected_seats = 7
        assert updated_membership.seats == expected_seats

        # But only charged for 2 more seats (4 limit - 2 current = 2 chargeable)
        # Verify calculate_prorata_seat_cost was called and invoice created
        # The pro-rata calculation internally uses calculate_chargeable_seats
        mock_billing_service.create_membership_invoice.assert_called_once()

    @patch("ams.memberships.forms.MembershipBillingService")
    def test_add_seats_zero_cost_when_at_max_charged_limit(
        self,
        mock_billing_service_class,
    ):
        """Test adding seats charges $0 when already at max_charged_seats."""
        # Arrange
        mock_billing_service = Mock()
        mock_billing_service.create_membership_invoice.return_value = None
        mock_billing_service_class.return_value = mock_billing_service

        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
            max_seats=None,  # No overall limit on seats
            max_charged_seats=5,  # But only charge for first 5
        )
        start_date = timezone.localdate()
        expiry_date = start_date + relativedelta(years=1)
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
            seats=5,  # Already at limit
            approved=True,
        )

        form = AddOrganisationSeatsForm(
            organisation=organisation,
            active_membership=membership,
            data={"seats_to_add": 10},  # Adding 10 more
        )

        # Act
        assert form.is_valid(), form.errors
        updated_membership, _invoice = form.save()

        # Assert
        # Membership should have 15 seats total
        updated_membership.refresh_from_db()
        expected_seats = 15
        assert updated_membership.seats == expected_seats

        # Verify NO invoice created (pro-rata cost is $0 when at limit)
        # When cost is $0, the form skips invoice creation
        mock_billing_service.create_membership_invoice.assert_not_called()

    @patch("ams.memberships.forms.MembershipBillingService")
    def test_add_seats_all_charged_without_limit(self, mock_billing_service_class):
        """Test adding seats charges for all when no max_charged_seats."""
        # Arrange
        mock_billing_service = Mock()
        mock_billing_service.create_membership_invoice.return_value = None
        mock_billing_service_class.return_value = mock_billing_service

        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
            max_seats=None,  # No overall limit on seats
            max_charged_seats=None,  # No limit on charging either
        )
        start_date = timezone.localdate()
        expiry_date = start_date + relativedelta(years=1)
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
            seats=10,
            approved=True,
        )

        form = AddOrganisationSeatsForm(
            organisation=organisation,
            active_membership=membership,
            data={"seats_to_add": 5},
        )

        # Act
        assert form.is_valid(), form.errors
        updated_membership, _invoice = form.save()

        # Assert
        updated_membership.refresh_from_db()
        expected_seats = 15
        assert updated_membership.seats == expected_seats
        # All 5 seats should be charged
        mock_billing_service.create_membership_invoice.assert_called_once()
