from unittest.mock import patch

import pytest
from django.test import Client
from django.test import override_settings
from django.urls import reverse

from ams.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestForumSSOLoginCallback:
    @override_settings(
        DISCOURSE_CONNECT_SECRET="test-secret",  # noqa: S106
        DISCOURSE_REDIRECT_DOMAIN="https://forum.example.com",
    )
    @patch(
        "ams.forum.views.sso_redirect_url",
        return_value="/session/sso_login?sso=x&sig=y",
    )
    @patch("ams.forum.views.sso_validate", return_value="nonce")
    def test_superuser_is_sent_as_admin(
        self,
        mock_sso_validate,
        mock_sso_redirect_url,
        client: Client,
    ):
        user = UserFactory(is_superuser=True)
        client.force_login(user)

        client.get(
            f"{reverse('forum:forum-sso-login-callback')}?sso=payload&sig=signature",
        )

        assert mock_sso_redirect_url.call_args.kwargs["admin"] == "true"

    @override_settings(
        DISCOURSE_CONNECT_SECRET="test-secret",  # noqa: S106
        DISCOURSE_REDIRECT_DOMAIN="https://forum.example.com",
    )
    @patch("ams.forum.views.user_has_active_membership", return_value=True)
    @patch(
        "ams.forum.views.sso_redirect_url",
        return_value="/session/sso_login?sso=x&sig=y",
    )
    @patch("ams.forum.views.sso_validate", return_value="nonce")
    def test_non_superuser_is_sent_as_non_admin(
        self,
        mock_sso_validate,
        mock_sso_redirect_url,
        mock_user_has_active_membership,
        client: Client,
    ):
        user = UserFactory(is_superuser=False)
        client.force_login(user)

        client.get(
            f"{reverse('forum:forum-sso-login-callback')}?sso=payload&sig=signature",
        )

        assert mock_sso_redirect_url.call_args.kwargs["admin"] == "false"
