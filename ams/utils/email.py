"""Email utilities for sending templated emails."""

import logging
from typing import Any

import html2text
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_templated_email(  # noqa: PLR0913
    subject: str,
    template_name: str,
    context: dict[str, Any],
    recipient_list: list[str],
    from_email: str | None = None,
    fail_silently: bool = False,  # noqa: FBT001, FBT002
) -> int:
    """
    Send an email using both HTML and text templates.

    This function renders both HTML and plain text versions of an email
    from templates and sends them using Django's email backend. If a .txt
    template doesn't exist, plaintext is automatically generated from the
    HTML template using html2text.

    Args:
        subject: The email subject line.
        template_name: The base name of the template (without extension).
                      For example, "organisation_invite" will load:
                      - emails/organisation_invite.html (compiled from MJML)
                      - emails/organisation_invite.txt (optional, auto-generated i
                        missing)
        context: Dictionary of context variables for template rendering.
        recipient_list: List of recipient email addresses.
        from_email: Sender email address. If None, uses DEFAULT_FROM_EMAIL.
        fail_silently: If False, raises exceptions on send errors.

    Returns:
        Number of successfully delivered messages (0 or 1).

    Raises:
        Exception: If fail_silently is False and sending fails.

    Settings:
        EMAIL_PLAINTEXT_IGNORE_LINKS: If True, excludes link URLs from plaintext.
                                     Default: False.
        EMAIL_PLAINTEXT_BODY_WIDTH: Maximum characters per line in plaintext.
                                   Default: 78.

    Example:
        >>> send_templated_email(
        ...     subject="Welcome!",
        ...     template_name="organisation_invite",
        ...     context={"organisation": org, "accept_url": url},
        ...     recipient_list=["user@example.com"],
        ... )
    """
    # Use default from email if not specified
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    # Render HTML version first (needed for auto-generation)
    try:
        html_content = render_to_string(
            f"emails/{template_name}.html",
            context,
        )
    except Exception:
        logger.exception(
            "Failed to render HTML template for email: %s",
            template_name,
        )
        if not fail_silently:
            raise
        return 0

    # Render or auto-generate text version
    try:
        # Try to render .txt template first
        text_content = render_to_string(
            f"emails/{template_name}.txt",
            context,
        )
    except TemplateDoesNotExist:
        # Auto-generate plaintext from HTML using html2text
        logger.info(
            "No .txt template found for %s, auto-generating from HTML",
            template_name,
        )
        h = html2text.HTML2Text()
        h.ignore_links = settings.EMAIL_PLAINTEXT_IGNORE_LINKS
        h.body_width = settings.EMAIL_PLAINTEXT_BODY_WIDTH
        text_content = h.handle(html_content)
    except Exception:
        logger.exception(
            "Failed to render text template for email: %s",
            template_name,
        )
        if not fail_silently:
            raise
        return 0

    # Create email message with both text and HTML
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=recipient_list,
    )
    msg.attach_alternative(html_content, "text/html")

    # Send email
    try:
        return msg.send(fail_silently=fail_silently)
    except Exception:
        logger.exception(
            "Failed to send email to %s using template: %s",
            recipient_list,
            template_name,
        )
        if not fail_silently:
            raise
        return 0
