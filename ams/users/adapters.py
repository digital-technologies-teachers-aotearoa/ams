from __future__ import annotations

import typing

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.template.loader import render_to_string

from ams.utils.email import send_templated_email

if typing.TYPE_CHECKING:
    from allauth.socialaccount.models import SocialLogin
    from django.http import HttpRequest

    from ams.users.models import User


class AccountAdapter(DefaultAccountAdapter):
    SUPPRESSED_MESSAGE_TEMPLATES = [
        "account/messages/logged_in.txt",
        "account/messages/logged_out.txt",
    ]

    def is_open_for_signup(self, request: HttpRequest) -> bool:
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)

    def add_message(
        self,
        request,
        level,
        message_template,
        message_context=None,
        extra_tags="",
    ):
        # Suppress the "successfully signed in" message
        if message_template in self.SUPPRESSED_MESSAGE_TEMPLATES:
            return
        super().add_message(
            request,
            level,
            message_template,
            message_context,
            extra_tags,
        )

    def send_mail(self, template_prefix, email, context):
        """Override to send HTML emails using MJML templates."""

        # Map allauth template prefixes to MJML template names
        template_map = {
            "account/email/email_confirmation": (
                "account/email/account_email_confirmation"
            ),
            "account/email/password_reset_key": (
                "account/email/account_password_reset"
            ),
            "account/email/password_changed": (
                "account/email/account_password_changed"
            ),
            "account/email/account_already_exists": (
                "account/email/account_already_exists"
            ),
        }

        template_name = template_map.get(template_prefix)

        if template_name:
            # Render subject using allauth's template
            subject = render_to_string(f"{template_prefix}_subject.txt", context)
            subject = "".join(subject.splitlines())

            # Send using MJML pipeline
            send_templated_email(
                subject=subject,
                template_name=template_name,
                context=context,
                recipient_list=[email],
            )
        else:
            # Fallback to default allauth behavior
            super().send_mail(template_prefix, email, context)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
    ) -> bool:
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)

    def populate_user(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
        data: dict[str, typing.Any],
    ) -> User:
        """
        Populates user information from social provider info.

        See: https://docs.allauth.org/en/latest/socialaccount/advanced.html#creating-and-populating-user-instances
        """
        user = super().populate_user(request, sociallogin, data)
        if not user.name:
            if name := data.get("name"):
                user.name = name
            elif first_name := data.get("first_name"):
                user.name = first_name
                if last_name := data.get("last_name"):
                    user.name += f" {last_name}"
        return user
