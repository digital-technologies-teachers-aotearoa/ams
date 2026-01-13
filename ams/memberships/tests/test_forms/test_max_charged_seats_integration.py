# ruff: noqa: PLR2004

"""Integration tests for max_charged_seats feature.

These tests verify the complete flow from membership creation through
multiple seat additions, ensuring correct billing at each step.
"""

from decimal import Decimal
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from django.utils import timezone

from ams.memberships.forms import AddOrganisationSeatsForm
from ams.memberships.forms import CreateOrganisationMembershipForm
from ams.memberships.tests.factories import MembershipOptionFactory
from ams.organisations.tests.factories import OrganisationFactory


@pytest.mark.django_db
class TestMaxChargedSeatsIntegration:
    """Integration tests for max_charged_seats billing flow."""

    @patch("ams.memberships.forms.MembershipBillingService")
    def test_complete_membership_lifecycle_with_max_charged_seats(
        self,
        mock_billing_service_class,
    ):
        """Test complete lifecycle: create membership, add seats multiple times.

        Scenario:
        - Create membership option: cost=$1000/year, max_charged_seats=4
        - Create membership with 2 seats → Charge $2000
        - Add 1 seat (total 3) → Charge pro-rata for 1 seat
        - Add 3 seats (total 6) → Charge pro-rata for 1 seat (4th), other 2 free
        - Add 5 more seats (total 11) → Charge $0 (already at limit)
        """
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
            max_charged_seats=4,  # But only charge for first 4
        )
        start_date = timezone.localdate()

        # Step 1: Create membership with 2 seats
        create_form = CreateOrganisationMembershipForm(
            organisation=organisation,
            data={
                "membership_option": membership_option.id,
                "start_date": start_date.isoformat(),
                "seat_count": 2,
            },
        )
        assert create_form.is_valid(), create_form.errors
        membership = create_form.save()

        # Assert Step 1: Charged for 2 seats
        call_args = mock_billing_service.create_membership_invoice.call_args
        assert call_args[0][2] == 2
        assert membership.seats == 2
        assert membership.chargeable_seats == 2
        assert membership.free_seats == 0

        mock_billing_service.reset_mock()

        # Step 2: Add 1 seat (total 3)
        add_form_1 = AddOrganisationSeatsForm(
            organisation=organisation,
            active_membership=membership,
            data={"seats_to_add": 1},
        )
        assert add_form_1.is_valid(), add_form_1.errors
        membership, _invoice = add_form_1.save()

        # Assert Step 2: Charged for 1 more seat
        membership.refresh_from_db()
        assert membership.seats == 3
        assert membership.chargeable_seats == 3
        assert membership.free_seats == 0

        mock_billing_service.reset_mock()

        # Step 3: Add 3 seats (total 6)
        add_form_2 = AddOrganisationSeatsForm(
            organisation=organisation,
            active_membership=membership,
            data={"seats_to_add": 3},
        )
        assert add_form_2.is_valid(), add_form_2.errors
        membership, _invoice = add_form_2.save()

        # Assert Step 3: Only 1 seat charged (4 max - 3 current = 1)
        membership.refresh_from_db()
        assert membership.seats == 6
        assert membership.chargeable_seats == 4
        assert membership.free_seats == 2

        mock_billing_service.reset_mock()

        # Step 4: Add 5 more seats (total 11)
        add_form_3 = AddOrganisationSeatsForm(
            organisation=organisation,
            active_membership=membership,
            data={"seats_to_add": 5},
        )
        assert add_form_3.is_valid(), add_form_3.errors
        membership, _invoice = add_form_3.save()

        # Assert Step 4: No additional seats charged (already at limit)
        membership.refresh_from_db()
        assert membership.seats == 11
        assert membership.chargeable_seats == 4
        assert membership.free_seats == 7

    @patch("ams.memberships.forms.MembershipBillingService")
    def test_membership_without_max_charged_seats(self, mock_billing_service_class):
        """Test normal behavior when max_charged_seats is not set."""
        # Arrange
        mock_billing_service = Mock()
        mock_billing_service.create_membership_invoice.return_value = None
        mock_billing_service_class.return_value = mock_billing_service

        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
            max_charged_seats=None,  # No limit
        )

        # Create with 5 seats
        create_form = CreateOrganisationMembershipForm(
            organisation=organisation,
            data={
                "membership_option": membership_option.id,
                "start_date": timezone.localdate().isoformat(),
                "seat_count": 5,
            },
        )
        assert create_form.is_valid()
        membership = create_form.save()

        # Assert: All 5 seats charged
        call_args = mock_billing_service.create_membership_invoice.call_args
        assert call_args[0][2] == 5

        mock_billing_service.reset_mock()

        # Add 5 more seats
        add_form = AddOrganisationSeatsForm(
            organisation=organisation,
            active_membership=membership,
            data={"seats_to_add": 5},
        )
        assert add_form.is_valid()
        membership, _invoice = add_form.save()

        # Assert: All 5 new seats charged
        membership.refresh_from_db()
        assert membership.seats == 10
        assert membership.chargeable_seats == 10
        assert membership.free_seats == 0
