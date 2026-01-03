"""Email utilities for organisation-related notifications."""

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ams.organisations.models import OrganisationMember

User = get_user_model()
logger = logging.getLogger(__name__)


def send_organisation_invite_email(request, member: OrganisationMember):
    """
    Send an invitation email to a member to join an organisation.

    Args:
        request: The HTTP request object (used to build absolute URLs).
        member: The OrganisationMember instance with invite details.
    """
    organisation = member.organisation
    invite_token = member.invite_token
    email = member.invite_email

    # Build the acceptance and decline URLs
    accept_url = request.build_absolute_uri(
        reverse(
            "organisations:accept_invite",
            kwargs={"invite_token": invite_token},
        ),
    )
    decline_url = request.build_absolute_uri(
        reverse(
            "organisations:decline_invite",
            kwargs={"invite_token": invite_token},
        ),
    )

    # Render email content
    subject = _(
        "You've been invited to join %(organisation_name)s",
    ) % {"organisation_name": organisation.name}

    # Render HTML email
    html_message = render_to_string(
        "organisations/emails/organisation_invite.html",
        {
            "organisation": organisation,
            "accept_url": accept_url,
            "decline_url": decline_url,
            "user_exists": member.user is not None,
        },
    )

    # Render plain text email
    text_message = render_to_string(
        "organisations/emails/organisation_invite.txt",
        {
            "organisation": organisation,
            "accept_url": accept_url,
            "decline_url": decline_url,
            "user_exists": member.user is not None,
        },
    )

    # Send email
    send_mail(
        subject=subject,
        message=text_message,
        from_email=None,  # Use DEFAULT_FROM_EMAIL
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )


def send_staff_organisation_created_notification(organisation, creator):
    """
    Send notification to staff when a new organisation is created.

    Args:
        organisation: The newly created Organisation instance.
        creator: The User who created the organisation.
    """
    # Check feature flag
    if not settings.NOTIFY_STAFF_ORG_EVENTS:
        return

    # Get staff emails
    staff_emails = list(
        User.objects.filter(is_staff=True).values_list("email", flat=True),
    )

    # Early return if no staff
    if not staff_emails:
        return

    # Build subject
    subject = _("New Organisation Created: %(organisation_name)s") % {
        "organisation_name": organisation.name,
    }

    # Build context
    context = {
        "organisation": organisation,
        "creator": creator,
        "creator_name": creator.get_full_name() or creator.username,
        "creator_email": creator.email,
    }

    # Render HTML email
    html_message = render_to_string(
        "organisations/emails/staff_organisation_created.html",
        context,
    )

    # Render plain text email
    text_message = render_to_string(
        "organisations/emails/staff_organisation_created.txt",
        context,
    )

    # Send email with error handling
    try:
        send_mail(
            subject=subject,
            message=text_message,
            from_email=None,  # Use DEFAULT_FROM_EMAIL
            recipient_list=staff_emails,
            html_message=html_message,
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "Failed to send staff notification for organisation creation: %s",
            organisation.uuid,
        )
        # Do not re-raise - allow user action to succeed


def send_staff_organisation_membership_notification(membership):
    """
    Send notification to staff when a new organisation membership is purchased.

    Args:
        membership: The newly created OrganisationMembership instance.
    """
    # Check feature flag
    if not settings.NOTIFY_STAFF_ORG_EVENTS:
        return

    # Get staff emails
    staff_emails = list(
        User.objects.filter(is_staff=True).values_list("email", flat=True),
    )

    # Early return if no staff
    if not staff_emails:
        return

    # Build subject
    subject = _("New Organisation Membership: %(organisation_name)s") % {
        "organisation_name": membership.organisation.name,
    }

    # Build context
    context = {
        "membership": membership,
        "organisation": membership.organisation,
        "membership_option": membership.membership_option,
        "seats": membership.max_seats,
        "start_date": membership.start_date,
        "expiry_date": membership.expiry_date,
        "cost": membership.membership_option.cost,
        "invoice_number": (
            membership.invoice.invoice_number if membership.invoice else None
        ),
    }

    # Render HTML email
    html_message = render_to_string(
        "organisations/emails/staff_organisation_membership_created.html",
        context,
    )

    # Render plain text email
    text_message = render_to_string(
        "organisations/emails/staff_organisation_membership_created.txt",
        context,
    )

    # Send email with error handling
    try:
        send_mail(
            subject=subject,
            message=text_message,
            from_email=None,  # Use DEFAULT_FROM_EMAIL
            recipient_list=staff_emails,
            html_message=html_message,
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
    if not settings.NOTIFY_STAFF_ORG_EVENTS:
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
        "new_total_seats": membership.max_seats,
        "prorata_cost": prorata_cost,
        "invoice_number": invoice.invoice_number if invoice else None,
        "expiry_date": membership.expiry_date,
    }

    # Render HTML email
    html_message = render_to_string(
        "organisations/emails/staff_organisation_seats_added.html",
        context,
    )

    # Render plain text email
    text_message = render_to_string(
        "organisations/emails/staff_organisation_seats_added.txt",
        context,
    )

    # Send email with error handling
    try:
        send_mail(
            subject=subject,
            message=text_message,
            from_email=None,  # Use DEFAULT_FROM_EMAIL
            recipient_list=staff_emails,
            html_message=html_message,
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "Failed to send staff notification for seats added to organisation: %s",
            organisation.uuid,
        )
        # Do not re-raise - allow user action to succeed
