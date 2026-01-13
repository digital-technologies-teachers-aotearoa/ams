"""Business logic services for memberships app."""

from decimal import ROUND_HALF_UP
from decimal import Decimal

from django.utils import timezone

from ams.memberships.models import OrganisationMembership


def calculate_chargeable_seats(
    membership: OrganisationMembership,
    seats_to_add: int,
) -> int:
    """Calculate how many of the seats being added should be charged.

    Takes into account max_charged_seats limit if set.

    Args:
        membership: The active organisation membership
        seats_to_add: Number of seats being added

    Returns:
        int: Number of seats that should be charged (may be less than seats_to_add)

    Examples:
        >>> # max_charged_seats=4, current seats=2, adding 3
        >>> # New total: 5 seats
        >>> # Already charged for: 2 seats
        >>> # Can charge for: 4 - 2 = 2 more seats
        >>> # Result: charge for 2 (not all 3)
    """
    max_charged = membership.membership_option.max_charged_seats

    # If no limit, charge for all seats
    if not max_charged:
        return seats_to_add

    max_charged = int(max_charged)
    current_seats = int(membership.seats)
    new_total_seats = current_seats + seats_to_add

    # Calculate current and new chargeable counts
    current_chargeable = min(current_seats, max_charged)
    new_chargeable = min(new_total_seats, max_charged)

    # Return the difference (additional seats to charge)
    return new_chargeable - current_chargeable


def calculate_prorata_seat_cost(
    membership: OrganisationMembership,
    seats_to_add: int,
) -> Decimal:
    """
    Calculate the pro-rata cost for additional seats based on remaining membership
    period.

    This function calculates what should be charged for adding seats to an existing
    organisation membership, pro-rated based on how much time remains in the
    membership period. If max_charged_seats is set, only charges for seats up to
    that limit.

    Formula: (cost_per_seat / total_days) * remaining_days * chargeable_seats

    Args:
        membership: The active organisation membership
        seats_to_add: Number of seats to add (int)

    Returns:
        Decimal: Pro-rated cost rounded to 2 decimal places

    Examples:
        >>> # Membership costs $1000/year, 6 months (182 days) remaining, adding 1 seat
        >>> # Daily rate: $1000 / 365 = $2.74/day
        >>> # Cost: $2.74 * 182 * 1 = ~$498.63

        >>> # With max_charged_seats=4, current=3, adding 3 seats
        >>> # Only 1 more seat is chargeable (3+3=6, but max_charged=4, diff=4-3=1)
        >>> # Cost: $2.74 * 182 * 1 = ~$498.63
    """
    membership_option = membership.membership_option
    cost_per_seat = membership_option.cost

    # Calculate how many seats should actually be charged
    chargeable_seats = calculate_chargeable_seats(membership, seats_to_add)

    # If no seats are chargeable, return 0
    if chargeable_seats <= 0:
        return Decimal("0.00")

    # Calculate total days in the membership period
    total_days = (membership.expiry_date - membership.start_date).days

    # Calculate remaining days
    today = timezone.localdate()
    remaining_days = (membership.expiry_date - today).days

    # Prevent division by zero (edge case)
    if total_days <= 0:
        return Decimal("0.00")

    # Calculate pro-rata cost
    # (cost_per_seat / total_days) x remaining_days x chargeable_seats
    daily_rate = cost_per_seat / Decimal(total_days)
    prorata_cost = daily_rate * Decimal(remaining_days) * Decimal(chargeable_seats)

    # Round to 2 decimal places for currency
    return prorata_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
