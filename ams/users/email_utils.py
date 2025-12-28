"""Email utilities for user-related notifications."""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ams.users.models import OrganisationMember


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

    # Build the acceptance URL
    accept_url = request.build_absolute_uri(
        reverse(
            "users:accept_organisation_invite",
            kwargs={"invite_token": invite_token},
        ),
    )

    # Render email content
    subject = _(
        "You've been invited to join %(organisation_name)s",
    ) % {"organisation_name": organisation.name}

    # Render HTML email
    html_message = render_to_string(
        "users/emails/organisation_invite.html",
        {
            "organisation": organisation,
            "accept_url": accept_url,
            "user_exists": member.user is not None,
        },
    )

    # Render plain text email
    text_message = render_to_string(
        "users/emails/organisation_invite.txt",
        {
            "organisation": organisation,
            "accept_url": accept_url,
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
