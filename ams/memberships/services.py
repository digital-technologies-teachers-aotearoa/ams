"""Business logic services for memberships app."""

from decimal import ROUND_HALF_UP
from decimal import Decimal

from django.utils import timezone

from ams.memberships.models import OrganisationMembership


def calculate_prorata_seat_cost(
    membership: OrganisationMembership,
    seats_to_add: int,
) -> Decimal:
    """
    Calculate the pro-rata cost for additional seats based on remaining membership
    period.

    This function calculates what should be charged for adding seats to an existing
    organisation membership, pro-rated based on how much time remains in the
    membership period.

    Formula: (cost_per_seat / total_days) * remaining_days * seats_to_add

    Args:
        membership: The active organisation membership
        seats_to_add: Number of seats to add (int)

    Returns:
        Decimal: Pro-rated cost rounded to 2 decimal places

    Examples:
        >>> # Membership costs $1000/year, 6 months (182 days) remaining, adding 1 seat
        >>> # Daily rate: $1000 / 365 = $2.74/day
        >>> # Cost: $2.74 * 182 * 1 = ~$498.63
    """
    membership_option = membership.membership_option
    cost_per_seat = membership_option.cost

    # Calculate total days in the membership period
    total_days = (membership.expiry_date - membership.start_date).days

    # Calculate remaining days
    today = timezone.localdate()
    remaining_days = (membership.expiry_date - today).days

    # Prevent division by zero (edge case)
    if total_days <= 0:
        return Decimal("0.00")

    # Calculate pro-rata cost
    # (cost_per_seat / total_days) x remaining_days x seats_to_add
    daily_rate = cost_per_seat / Decimal(total_days)
    prorata_cost = daily_rate * Decimal(remaining_days) * Decimal(seats_to_add)

    # Round to 2 decimal places for currency
    return prorata_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
