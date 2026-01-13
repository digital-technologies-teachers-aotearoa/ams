"""Tests for memberships service functions."""

from decimal import Decimal
from unittest.mock import patch

import pytest
from dateutil.relativedelta import relativedelta
from django.utils import timezone

from ams.memberships.services import calculate_chargeable_seats
from ams.memberships.services import calculate_prorata_seat_cost
from ams.memberships.tests.factories import MembershipOptionFactory
from ams.memberships.tests.factories import OrganisationMembershipFactory
from ams.organisations.tests.factories import OrganisationFactory


@pytest.mark.django_db
class TestCalculateProrataSeatCost:
    """Tests for calculate_prorata_seat_cost function."""

    def test_start_of_period_single_seat(self):
        """Test pro-rata at start of period is close to full cost for 1 seat."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
        )

        # Create membership starting today
        start_date = timezone.localdate()
        expiry_date = start_date + relativedelta(years=1)

        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
        )

        # At the start of the period, pro-rata should be close to full cost
        prorata_cost = calculate_prorata_seat_cost(membership, 1)

        # Should be approximately $1000 (may be slightly less due to today calculation)
        assert prorata_cost >= Decimal("995.00")
        assert prorata_cost <= Decimal("1000.00")

    def test_half_period_single_seat(self):
        """Test pro-rata at midpoint is approximately 50% of full cost."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
        )

        # Create membership that started 6 months ago (halfway through)
        start_date = timezone.localdate() - relativedelta(months=6)
        expiry_date = start_date + relativedelta(years=1)

        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
        )

        prorata_cost = calculate_prorata_seat_cost(membership, 1)

        # Should be approximately $500 (half of $1000)
        # Allow some variance for exact day calculations
        assert prorata_cost >= Decimal("490.00")
        assert prorata_cost <= Decimal("510.00")

    def test_near_expiry_single_seat(self):
        """Test pro-rata near end of period is small fraction of full cost."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
        )

        # Create membership with only 30 days remaining
        expiry_date = timezone.localdate() + relativedelta(days=30)
        start_date = expiry_date - relativedelta(years=1)

        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
        )

        prorata_cost = calculate_prorata_seat_cost(membership, 1)

        # Should be approximately (1000/365) * 30 = ~$82.19
        assert prorata_cost >= Decimal("80.00")
        assert prorata_cost <= Decimal("85.00")

    def test_precision_multiple_seats(self):
        """Test pro-rata calculation rounds to 2 decimal places."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("100.00"),
            duration={"days": 365},
        )

        # Create a scenario that would result in many decimal places
        start_date = timezone.localdate() - relativedelta(days=100)
        expiry_date = start_date + relativedelta(days=365)

        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
        )

        prorata_cost = calculate_prorata_seat_cost(membership, 3)

        # Check that it's a Decimal with exactly 2 decimal places
        assert isinstance(prorata_cost, Decimal)
        assert prorata_cost == prorata_cost.quantize(Decimal("0.01"))

    def test_multiple_seats_5(self):
        """Test calculation with 5 seats."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("100.00"),
            duration={"years": 1},
        )

        start_date = timezone.localdate()
        expiry_date = start_date + relativedelta(years=1)

        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
        )

        prorata_cost = calculate_prorata_seat_cost(membership, 5)

        # Should be approximately 5x the single seat cost
        # At start of period, should be close to $500 (5 * $100)
        assert prorata_cost >= Decimal("495.00")
        assert prorata_cost <= Decimal("500.00")

    def test_multiple_seats_10(self):
        """Test calculation with 10 seats."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("100.00"),
            duration={"years": 1},
        )

        start_date = timezone.localdate()
        expiry_date = start_date + relativedelta(years=1)

        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
        )

        prorata_cost = calculate_prorata_seat_cost(membership, 10)

        # Should be approximately 10x the single seat cost
        # At start of period, should be close to $1000 (10 * $100)
        assert prorata_cost >= Decimal("990.00")
        assert prorata_cost <= Decimal("1000.00")

    def test_large_seat_count_100(self):
        """Test calculation with very large seat count (100 seats)."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("50.00"),
            duration={"years": 1},
        )

        start_date = timezone.localdate()
        expiry_date = start_date + relativedelta(years=1)

        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
        )

        prorata_cost = calculate_prorata_seat_cost(membership, 100)

        # Should be approximately 100x the single seat cost
        # At start of period, should be close to $5000 (100 * $50)
        assert prorata_cost >= Decimal("4950.00")
        assert prorata_cost <= Decimal("5000.00")

    def test_very_large_seat_count_1000(self):
        """Test calculation with 1000+ seats."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("10.00"),
            duration={"years": 1},
        )

        start_date = timezone.localdate()
        expiry_date = start_date + relativedelta(years=1)

        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
        )

        prorata_cost = calculate_prorata_seat_cost(membership, 1000)

        # Should be approximately 1000x the single seat cost
        # At start of period, should be close to $10000 (1000 * $10)
        assert prorata_cost >= Decimal("9900.00")
        assert prorata_cost <= Decimal("10000.00")

    def test_days_duration(self):
        """Test with day-based membership duration."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("100.00"),
            duration={"days": 30},
        )

        start_date = timezone.localdate()
        expiry_date = start_date + relativedelta(days=30)

        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
        )

        prorata_cost = calculate_prorata_seat_cost(membership, 1)

        # At start of 30-day period, should be close to full $100
        assert prorata_cost >= Decimal("98.00")
        assert prorata_cost <= Decimal("100.00")

    def test_months_duration(self):
        """Test with month-based membership duration."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("500.00"),
            duration={"months": 6},
        )

        start_date = timezone.localdate()
        expiry_date = start_date + relativedelta(months=6)

        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
        )

        prorata_cost = calculate_prorata_seat_cost(membership, 1)

        # At start of 6-month period, should be close to full $500
        assert prorata_cost >= Decimal("495.00")
        assert prorata_cost <= Decimal("500.00")

    def test_years_duration(self):
        """Test with year-based membership duration."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1200.00"),
            duration={"years": 2},
        )

        start_date = timezone.localdate()
        expiry_date = start_date + relativedelta(years=2)

        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
        )

        prorata_cost = calculate_prorata_seat_cost(membership, 1)

        # At start of 2-year period, should be close to full $1200
        assert prorata_cost >= Decimal("1190.00")
        assert prorata_cost <= Decimal("1200.00")

    @patch("ams.memberships.services.timezone.localdate")
    def test_leap_year_scenario(self, mock_localdate):
        """Test calculations work correctly during leap year."""
        # Set current date to a leap year
        mock_localdate.return_value = timezone.datetime(2024, 2, 29).date()

        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("366.00"),  # $1 per day in leap year
            duration={"days": 366},
        )

        start_date = timezone.datetime(2024, 1, 1).date()
        expiry_date = timezone.datetime(2024, 12, 31).date()

        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
        )

        prorata_cost = calculate_prorata_seat_cost(membership, 1)

        # Should calculate correctly based on remaining days
        # From Feb 29 to Dec 31 (306 days remaining out of 366)
        # Expected: (366/365) * 306 * 1 ≈ $306.84
        assert prorata_cost >= Decimal("305.00")
        assert prorata_cost <= Decimal("308.00")

    def test_zero_cost_membership(self):
        """Test behavior with zero-cost (free) membership."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("0.00"),
            duration={"years": 1},
        )

        start_date = timezone.localdate()
        expiry_date = start_date + relativedelta(years=1)

        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
        )

        prorata_cost = calculate_prorata_seat_cost(membership, 5)

        # Free membership should always cost $0
        assert prorata_cost == Decimal("0.00")

    def test_expiring_today(self):
        """Test edge case where membership expires today."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
        )

        # Membership expires today
        expiry_date = timezone.localdate()
        start_date = expiry_date - relativedelta(years=1)

        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
        )

        prorata_cost = calculate_prorata_seat_cost(membership, 1)

        # 0 days remaining should result in $0 cost
        assert prorata_cost == Decimal("0.00")

    def test_expiring_tomorrow(self):
        """Test edge case with only 1 day remaining."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("365.00"),  # $1 per day
            duration={"days": 365},
        )

        # Membership expires tomorrow
        expiry_date = timezone.localdate() + relativedelta(days=1)
        start_date = expiry_date - relativedelta(days=365)

        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
        )

        prorata_cost = calculate_prorata_seat_cost(membership, 1)

        # 1 day remaining should be approximately $1
        assert prorata_cost >= Decimal("0.99")
        assert prorata_cost <= Decimal("1.01")

    def test_two_days_remaining(self):
        """Test with 2 days remaining in period."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("365.00"),  # $1 per day
            duration={"days": 365},
        )

        # Membership expires in 2 days
        expiry_date = timezone.localdate() + relativedelta(days=2)
        start_date = expiry_date - relativedelta(days=365)

        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
        )

        prorata_cost = calculate_prorata_seat_cost(membership, 1)

        # 2 days remaining should be approximately $2
        assert prorata_cost >= Decimal("1.98")
        assert prorata_cost <= Decimal("2.02")

    def test_expired_membership(self):
        """Test edge case where membership has already expired."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
        )

        # Membership expired yesterday
        expiry_date = timezone.localdate() - relativedelta(days=1)
        start_date = expiry_date - relativedelta(years=1)

        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
        )

        prorata_cost = calculate_prorata_seat_cost(membership, 1)

        # Expired membership should result in negative or $0 cost
        # (The function will calculate negative days, which should be handled)
        # Based on current implementation, this would give negative cost
        # but practically should be prevented at validation level
        assert prorata_cost <= Decimal("0.00")

    def test_multi_year_at_start(self):
        """Test long duration membership at start of period."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("5000.00"),
            duration={"years": 5},
        )

        start_date = timezone.localdate()
        expiry_date = start_date + relativedelta(years=5)

        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
        )

        prorata_cost = calculate_prorata_seat_cost(membership, 1)

        # At start of 5-year period, should be close to full $5000
        assert prorata_cost >= Decimal("4950.00")
        assert prorata_cost <= Decimal("5000.00")

    def test_complex_decimal_precision(self):
        """Test costs that result in many decimal places are rounded correctly."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("99.99"),  # Awkward price
            duration={"days": 333},  # Awkward duration
        )

        start_date = timezone.localdate() - relativedelta(days=111)
        expiry_date = start_date + relativedelta(days=333)

        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
        )

        # Adding 7 seats with complex calculation
        prorata_cost = calculate_prorata_seat_cost(membership, 7)

        # Verify it's properly rounded to 2 decimal places
        assert isinstance(prorata_cost, Decimal)
        assert prorata_cost == prorata_cost.quantize(Decimal("0.01"))
        # Should be a reasonable value
        assert prorata_cost > Decimal("0.00")
        assert prorata_cost < Decimal("700.00")  # Can't exceed 7 * 99.99

    def test_zero_total_days_edge_case(self):
        """Test edge case where start_date equals expiry_date."""
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"days": 1},
        )

        # Same start and expiry date (edge case)
        date = timezone.localdate()

        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=date,
            expiry_date=date,
        )

        prorata_cost = calculate_prorata_seat_cost(membership, 1)

        # Should return $0 to avoid division by zero
        assert prorata_cost == Decimal("0.00")

    def test_prorata_with_max_charged_seats_limit(self):
        """Test pro-rata calculation respects max_charged_seats limit."""
        # Arrange
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
            max_charged_seats=5,
        )
        start_date = timezone.localdate()
        expiry_date = start_date + relativedelta(years=1)
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
            seats=0,
            approved=True,
        )
        # Act
        prorata_cost = calculate_prorata_seat_cost(membership, 10)
        # Assert
        # Should calculate for 5 seats (max_charged), not 10
        # At start of period, should be close to $5000 (5 x $1000)
        assert prorata_cost >= Decimal("4975.00")
        assert prorata_cost <= Decimal("5000.00")

    def test_prorata_with_partial_charge_when_near_limit(self):
        """Test pro-rata when only some seats are chargeable."""
        # Arrange
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
            seats=3,  # Already have 3
            approved=True,
        )
        # Act
        prorata_cost = calculate_prorata_seat_cost(membership, 5)
        # Assert
        # Can only charge for 1 more seat (4 - 3 = 1)
        # At start of period, should be close to $1000 (1 x $1000)
        assert prorata_cost >= Decimal("995.00")
        assert prorata_cost <= Decimal("1000.00")

    def test_prorata_zero_when_at_max_charged_limit(self):
        """Test pro-rata returns $0 when already at max_charged_seats limit."""
        # Arrange
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
            max_charged_seats=5,
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
        # Act
        prorata_cost = calculate_prorata_seat_cost(membership, 10)
        # Assert
        assert prorata_cost == Decimal("0.00")  # No charge for additional seats

    def test_prorata_zero_cost_membership_with_max_charged(self):
        """Test pro-rata with free membership that has max_charged_seats set."""
        # Arrange
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("0.00"),  # Free membership
            duration={"years": 1},
            max_charged_seats=5,  # Limit set but doesn't matter
        )
        start_date = timezone.localdate()
        expiry_date = start_date + relativedelta(years=1)
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            start_date=start_date,
            expiry_date=expiry_date,
            seats=0,
            approved=True,
        )
        # Act
        prorata_cost = calculate_prorata_seat_cost(membership, 10)
        # Assert
        assert prorata_cost == Decimal("0.00")


@pytest.mark.django_db
class TestCalculateChargeableSeats:
    """Tests for calculate_chargeable_seats function."""

    def test_calculate_chargeable_seats_no_limit(self):
        """Test that all seats are chargeable when no limit is set."""
        # Arrange
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
            max_charged_seats=None,
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            seats=5,
            approved=True,
        )
        # Act
        chargeable = calculate_chargeable_seats(membership, 3)
        # Assert
        expected_chargable = 3
        assert chargeable == expected_chargable

    def test_calculate_chargeable_seats_respects_limit(self):
        """Test that chargeable seats caps at max_charged_seats."""
        # Arrange
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            max_charged_seats=4,
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            seats=0,  # Starting with no seats
            approved=True,
        )
        # Act
        chargeable = calculate_chargeable_seats(membership, 10)
        # Assert
        expected_chargable = 4
        assert chargeable == expected_chargable

    def test_calculate_chargeable_seats_accounts_for_current(self):
        """Test that current seats are accounted for when calculating chargeable."""
        # Arrange
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            max_charged_seats=4,
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            seats=2,  # Already have 2 seats
            approved=True,
        )
        # Act
        chargeable = calculate_chargeable_seats(membership, 5)
        # Assert
        # Current: 2, Adding: 5, New total: 7
        # Max charged: 4, Already charged: 2, Can charge: 4-2=2
        expected_chargable = 2
        assert chargeable == expected_chargable

    def test_calculate_chargeable_seats_zero_when_at_limit(self):
        """Test that no seats are chargeable when already at limit."""
        # Arrange
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            max_charged_seats=5,
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            seats=5,  # Already at limit
            approved=True,
        )
        # Act
        chargeable = calculate_chargeable_seats(membership, 10)
        # Assert
        assert chargeable == 0

    def test_calculate_chargeable_seats_partial_near_limit(self):
        """Test partial charging when adding seats near the limit."""
        # Arrange
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            max_charged_seats=10,
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            seats=8,  # 8 out of 10
            approved=True,
        )
        # Act
        chargeable = calculate_chargeable_seats(membership, 5)
        # Assert
        # Current: 8, Adding: 5, New total: 13
        # Max charged: 10, Already charged: 8, Can charge: 10-8=2
        expected_chargable = 2
        assert chargeable == expected_chargable

    def test_calculate_chargeable_seats_zero_to_add(self):
        """Test behavior when adding zero seats."""
        # Arrange
        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            max_charged_seats=5,
        )
        membership = OrganisationMembershipFactory(
            organisation=organisation,
            membership_option=membership_option,
            seats=3,
            approved=True,
        )
        # Act
        chargeable = calculate_chargeable_seats(membership, 0)
        # Assert
        assert chargeable == 0
