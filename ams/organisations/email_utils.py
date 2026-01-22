"""Email utilities for organisation-related notifications."""

import logging
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ams.organisations.models import OrganisationMember
from ams.utils.email import send_templated_email

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
    user_exists = member.user is not None

    # Build the acceptance and decline URLs
    accept_path = reverse(
        "organisations:accept_invite",
        kwargs={"invite_token": invite_token},
    )
    decline_path = reverse(
        "organisations:decline_invite",
        kwargs={"invite_token": invite_token},
    )

    # Build absolute URLs
    accept_absolute_url = request.build_absolute_uri(accept_path)
    decline_absolute_url = request.build_absolute_uri(decline_path)

    # For existing users, wrap accept/decline URLs with login redirect
    if user_exists:
        login_path = reverse("account_login")
        accept_url = request.build_absolute_uri(
            f"{login_path}?{urlencode({'next': accept_path})}",
        )
        decline_url = request.build_absolute_uri(
            f"{login_path}?{urlencode({'next': decline_path})}",
        )
    else:
        # For new users, link directly to accept/decline (which will redirect to login)
        accept_url = accept_absolute_url
        decline_url = decline_absolute_url

    # Build signup and email settings URLs
    signup_url = request.build_absolute_uri(reverse("account_signup"))
    email_settings_url = request.build_absolute_uri(reverse("account_email"))

    # Build subject and send email
    subject = _(
        "You've been invited to join %(organisation_name)s",
    ) % {"organisation_name": organisation.name}

    send_templated_email(
        subject=subject,
        template_name="organisations/emails/organisation_invite",
        context={
            "organisation": organisation,
            "accept_url": accept_url,
            "decline_url": decline_url,
            "signup_url": signup_url,
            "email_settings_url": email_settings_url,
            "user_exists": user_exists,
        },
        recipient_list=[email],
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
    if not settings.NOTIFY_STAFF_ORGANISATION_EVENTS:
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

    # Send email with error handling
    try:
        send_templated_email(
            subject=subject,
            template_name="organisations/emails/staff_organisation_created",
            context=context,
            recipient_list=staff_emails,
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "Failed to send staff notification for organisation creation: %s",
            organisation.uuid,
        )
        # Do not re-raise - allow user action to succeed
