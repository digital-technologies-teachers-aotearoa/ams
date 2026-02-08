"""Helper functions for terms and conditions."""

from typing import TYPE_CHECKING

from django.utils import timezone

from ams.terms.models import TermAcceptance
from ams.terms.models import TermVersion

if TYPE_CHECKING:
    from ams.users.models import User


def get_pending_term_versions_for_user(user: "User") -> "list[TermVersion]":
    """
    Get all required TermVersions that user has not yet accepted.

    This is the single source of truth for determining which terms
    a user needs to accept.

    Returns only the LATEST version of each term, where latest is determined
    by the most recent date_active timestamp. A user only needs to accept
    the current latest version of each term, not all historical versions.

    Returns TermVersions that are:
    - Active (is_active=True)
    - Current (date_active <= now)
    - Latest for their term (most recent date_active)
    - Not yet accepted by the user

    Results are ordered deterministically by term.key to ensure
    consistent presentation order.

    Args:
        user: The User instance to check

    Returns:
        List of TermVersion instances pending acceptance
    """

    # Anonymous users don't need to accept terms
    if not user.is_authenticated:
        return []

    now = timezone.now()

    # Get all current (active and enforceable) term versions
    current_versions = TermVersion.objects.filter(
        is_active=True,
        date_active__lte=now,
    ).select_related("term")

    # Group versions by term and get the latest version for each term
    # Latest = most recent date_active
    latest_versions_by_term = {}
    for version in current_versions:
        term_id = version.term_id
        if (
            term_id not in latest_versions_by_term
            or version.date_active > latest_versions_by_term[term_id].date_active
        ):
            latest_versions_by_term[term_id] = version

    # Get only the latest versions
    latest_versions = list(latest_versions_by_term.values())

    # Get all term versions this user has already accepted
    accepted_version_ids = set(
        TermAcceptance.objects.filter(user=user).values_list(
            "term_version_id",
            flat=True,
        ),
    )

    # Filter to only pending versions (latest versions not yet accepted)
    pending_versions = [
        version for version in latest_versions if version.id not in accepted_version_ids
    ]

    # Sort deterministically by term.key
    # This ensures users always see terms in the same order
    pending_versions.sort(key=lambda v: v.term.key)

    return pending_versions


def get_latest_term_versions() -> "list[TermVersion]":
    """
    Get the latest version of each term.

    Returns the most recent (by date_active) active term version for each term.
    This is used for displaying all current terms to users, regardless of
    whether they've accepted them.

    Returns TermVersions that are:
    - Active (is_active=True)
    - Current (date_active <= now)
    - Latest for their term (most recent date_active)

    Results are ordered deterministically by term.key.

    Returns:
        List of TermVersion instances (latest version per term)
    """
    now = timezone.now()

    # Get all current (active and enforceable) term versions
    current_versions = TermVersion.objects.filter(
        is_active=True,
        date_active__lte=now,
    ).select_related("term")

    # Group versions by term and get the latest version for each term
    # Latest = most recent date_active
    latest_versions_by_term = {}
    for version in current_versions:
        term_id = version.term_id
        if (
            term_id not in latest_versions_by_term
            or version.date_active > latest_versions_by_term[term_id].date_active
        ):
            latest_versions_by_term[term_id] = version

    # Get only the latest versions
    latest_versions = list(latest_versions_by_term.values())

    # Sort deterministically by term.key
    latest_versions.sort(key=lambda v: v.term.key)

    return latest_versions
