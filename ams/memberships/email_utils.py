"""Email utilities for membership-related notifications."""

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from ams.utils.email import send_templated_email

User = get_user_model()
logger = logging.getLogger(__name__)


def send_staff_organisation_membership_notification(membership):
    """
    Send notification to staff when a new organisation membership is purchased.

    Args:
        membership: The newly created OrganisationMembership instance.
    """
    # Check if approval is required (free membership pending approval)
    requires_approval = (
        membership.approved_datetime is None and membership.membership_option.cost == 0
    )

    # Always send email if approval is required, even if notifications are disabled
    # Otherwise, check feature flag
    if not requires_approval and not settings.NOTIFY_STAFF_MEMBERSHIP_EVENTS:
        return

    # Get staff emails
    staff_emails = list(
        User.objects.filter(is_staff=True).values_list("email", flat=True),
    )

    # Early return if no staff
    if not staff_emails:
        return

    # Build subject - add "REQUIRES APPROVAL" prefix if approval is needed
    if requires_approval:
        subject = _(
            "REQUIRES APPROVAL: Organisation Membership - %(organisation_name)s",
        ) % {
            "organisation_name": membership.organisation.name,
        }
    else:
        subject = _("New Organisation Membership: %(organisation_name)s") % {
            "organisation_name": membership.organisation.name,
        }

    # Build context
    context = {
        "membership": membership,
        "organisation": membership.organisation,
        "membership_option": membership.membership_option,
        "seats": membership.seats,
        "start_date": membership.start_date,
        "expiry_date": membership.expiry_date,
        # Pricing fields
        "cost_per_seat": membership.membership_option.cost,
        "chargeable_seats": membership.chargeable_seats,
        "total_cost": membership.membership_option.cost * membership.chargeable_seats,
        "free_seats": membership.free_seats,
        "has_free_seats": membership.free_seats > 0,
        # Other fields
        "invoice_number": (
            membership.invoices.first().invoice_number
            if membership.invoices.exists()
            else None
        ),
        "requires_approval": membership.approved_datetime is None,
        "is_free": membership.membership_option.cost == 0,
    }

    # Send email with error handling
    try:
        send_templated_email(
            subject=subject,
            template_name="memberships/emails/staff_organisation_membership_created",
            context=context,
            recipient_list=staff_emails,
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "Failed to send staff notification for organisation membership: %s",
            membership.organisation.uuid,
        )
        # Do not re-raise - allow user action to succeed


def send_staff_organisation_seats_added_notification(
    organisation,
    membership,
    seats_added,
    prorata_cost,
    invoice,
):
    """
    Send notification to staff when additional seats are purchased for an organisation.

    Args:
        organisation: The Organisation instance.
        membership: The OrganisationMembership instance.
        seats_added: Number of seats that were added (int).
        prorata_cost: The pro-rated cost calculated (Decimal).
        invoice: The Invoice instance (or None if no invoice created).
    """
    # Check feature flag
    if not settings.NOTIFY_STAFF_MEMBERSHIP_EVENTS:
        return

    # Get staff emails
    staff_emails = list(
        User.objects.filter(is_staff=True).values_list("email", flat=True),
    )

    # Early return if no staff
    if not staff_emails:
        return

    # Build subject
    subject = _("Seats Added to Organisation: %(organisation_name)s") % {
        "organisation_name": organisation.name,
    }

    # Build context
    context = {
        "organisation": organisation,
        "membership": membership,
        "membership_option": membership.membership_option,
        "seats_added": seats_added,
        "new_total_seats": membership.seats,
        "prorata_cost": prorata_cost,
        "invoice_number": invoice.invoice_number if invoice else None,
        "expiry_date": membership.expiry_date,
    }

    # Send email with error handling
    try:
        send_templated_email(
            subject=subject,
            template_name="memberships/emails/staff_organisation_seats_added",
            context=context,
            recipient_list=staff_emails,
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "Failed to send staff notification for seats added to organisation: %s",
            organisation.uuid,
        )
        # Do not re-raise - allow user action to succeed


def send_staff_individual_membership_notification(membership):
    """
    Send notification to staff when a new individual membership is purchased.

    Args:
        membership: The newly created IndividualMembership instance.
    """
    # Check if approval is required (free membership pending approval)
    requires_approval = (
        membership.approved_datetime is None and membership.membership_option.cost == 0
    )

    # Always send email if approval is required, even if notifications are disabled
    # Otherwise, check feature flag
    if not requires_approval and not settings.NOTIFY_STAFF_MEMBERSHIP_EVENTS:
        return

    # Get staff emails
    staff_emails = list(
        User.objects.filter(is_staff=True).values_list("email", flat=True),
    )

    # Early return if no staff
    if not staff_emails:
        return

    # Build subject - add "REQUIRES APPROVAL" prefix if approval is needed
    if requires_approval:
        subject = _("REQUIRES APPROVAL: Individual Membership - %(user_name)s") % {
            "user_name": membership.user.get_full_name(),
        }
    else:
        subject = _("New Individual Membership: %(user_name)s") % {
            "user_name": membership.user.get_full_name(),
        }

    # Build context
    context = {
        "membership": membership,
        "user": membership.user,
        "user_full_name": membership.user.get_full_name(),
        "user_email": membership.user.email,
        "membership_option": membership.membership_option,
        "start_date": membership.start_date,
        "expiry_date": membership.expiry_date,
        "cost": membership.membership_option.cost,
        "invoice_number": (
            membership.invoices.first().invoice_number
            if membership.invoices.exists()
            else None
        ),
        "requires_approval": membership.approved_datetime is None,
        "is_free": membership.membership_option.cost == 0,
    }

    # Send email with error handling
    try:
        send_templated_email(
            subject=subject,
            template_name="memberships/emails/staff_individual_membership_created",
            context=context,
            recipient_list=staff_emails,
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "Failed to send staff notification for individual membership: %s",
            membership.user.pk,
        )
        # Do not re-raise - allow user action to succeed
