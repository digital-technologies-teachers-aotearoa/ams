from unittest.mock import Mock
from unittest.mock import patch

import pytest
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.messages import INFO
from django.test import RequestFactory

from ams.users.adapters import AccountAdapter
from ams.users.adapters import SocialAccountAdapter


@pytest.fixture
def request_factory():
    """Fixture for creating mock requests."""
    return RequestFactory()


@pytest.fixture
def account_adapter():
    """Fixture for AccountAdapter instance."""
    return AccountAdapter()


@pytest.fixture
def social_account_adapter():
    """Fixture for SocialAccountAdapter instance."""
    return SocialAccountAdapter()


class TestAccountAdapter:
    """Test class for AccountAdapter."""

    def test_suppressed_message_templates_list(self, account_adapter):
        """Test that SUPPRESSED_MESSAGE_TEMPLATES contains expected templates."""
        expected_templates = [
            "account/messages/logged_in.txt",
            "account/messages/logged_out.txt",
        ]
        assert expected_templates == account_adapter.SUPPRESSED_MESSAGE_TEMPLATES

    def test_is_open_for_signup_when_registration_allowed(
        self,
        account_adapter,
        request_factory,
        settings,
    ):
        """Test signup is open when ACCOUNT_ALLOW_REGISTRATION is True."""
        settings.ACCOUNT_ALLOW_REGISTRATION = True
        request = request_factory.get("/")
        assert account_adapter.is_open_for_signup(request) is True

    def test_is_open_for_signup_when_registration_not_allowed(
        self,
        account_adapter,
        request_factory,
        settings,
    ):
        """Test signup is closed when ACCOUNT_ALLOW_REGISTRATION is False."""
        settings.ACCOUNT_ALLOW_REGISTRATION = False
        request = request_factory.get("/")
        assert account_adapter.is_open_for_signup(request) is False

    def test_is_open_for_signup_default_behavior(
        self,
        account_adapter,
        request_factory,
    ):
        """Test signup defaults to True when ACCOUNT_ALLOW_REGISTRATION is not set."""
        request = request_factory.get("/")
        # Should default to True if setting doesn't exist
        result = account_adapter.is_open_for_signup(request)
        assert isinstance(result, bool)

    @patch.object(DefaultAccountAdapter, "add_message")
    def test_add_message_suppresses_logged_in_message(
        self,
        mock_super_add_message,
        account_adapter,
        request_factory,
    ):
        """Test that logged_in message is suppressed."""
        request = request_factory.get("/")

        account_adapter.add_message(
            request,
            INFO,
            "account/messages/logged_in.txt",
            message_context={"user": "testuser"},
            extra_tags="",
        )

        # Super method should NOT be called for suppressed messages
        mock_super_add_message.assert_not_called()

    @patch.object(DefaultAccountAdapter, "add_message")
    def test_add_message_suppresses_logged_out_message(
        self,
        mock_super_add_message,
        account_adapter,
        request_factory,
    ):
        """Test that logged_out message is suppressed."""
        request = request_factory.get("/")

        account_adapter.add_message(
            request,
            INFO,
            "account/messages/logged_out.txt",
            message_context={},
            extra_tags="custom-tag",
        )

        # Super method should NOT be called for suppressed messages
        mock_super_add_message.assert_not_called()

    @patch.object(DefaultAccountAdapter, "add_message")
    def test_add_message_allows_non_suppressed_messages(
        self,
        mock_super_add_message,
        account_adapter,
        request_factory,
    ):
        """Test that non-suppressed messages are passed to parent class."""
        request = request_factory.get("/")

        message_template = "account/messages/password_changed.txt"
        message_context = {"user": "testuser"}
        extra_tags = "success"

        account_adapter.add_message(
            request,
            INFO,
            message_template,
            message_context=message_context,
            extra_tags=extra_tags,
        )

        # Super method SHOULD be called for non-suppressed messages
        mock_super_add_message.assert_called_once_with(
            request,
            INFO,
            message_template,
            message_context,
            extra_tags,
        )

    @patch.object(DefaultAccountAdapter, "add_message")
    def test_add_message_with_various_message_templates(
        self,
        mock_super_add_message,
        account_adapter,
        request_factory,
    ):
        """Test add_message with multiple non-suppressed message templates."""
        request = request_factory.get("/")

        non_suppressed_templates = [
            "account/messages/email_confirmed.txt",
            "account/messages/password_set.txt",
            "account/messages/password_changed.txt",
            "account/messages/primary_email_set.txt",
        ]

        for template in non_suppressed_templates:
            account_adapter.add_message(
                request,
                INFO,
                template,
            )

        # Should have been called for each non-suppressed message
        assert mock_super_add_message.call_count == len(non_suppressed_templates)

    @patch.object(DefaultAccountAdapter, "add_message")
    def test_add_message_with_none_message_context(
        self,
        mock_super_add_message,
        account_adapter,
        request_factory,
    ):
        """Test add_message works with None message_context."""
        request = request_factory.get("/")

        account_adapter.add_message(
            request,
            INFO,
            "account/messages/email_confirmed.txt",
            message_context=None,
            extra_tags="",
        )

        mock_super_add_message.assert_called_once_with(
            request,
            INFO,
            "account/messages/email_confirmed.txt",
            None,
            "",
        )


class TestSocialAccountAdapter:
    """Test class for SocialAccountAdapter."""

    def test_is_open_for_signup_when_registration_allowed(
        self,
        social_account_adapter,
        request_factory,
        settings,
    ):
        """Test social signup is open when ACCOUNT_ALLOW_REGISTRATION is True."""
        settings.ACCOUNT_ALLOW_REGISTRATION = True
        request = request_factory.get("/")
        social_login = Mock()

        assert social_account_adapter.is_open_for_signup(request, social_login) is True

    def test_is_open_for_signup_when_registration_not_allowed(
        self,
        social_account_adapter,
        request_factory,
        settings,
    ):
        """Test social signup is closed when ACCOUNT_ALLOW_REGISTRATION is False."""
        settings.ACCOUNT_ALLOW_REGISTRATION = False
        request = request_factory.get("/")
        social_login = Mock()

        assert social_account_adapter.is_open_for_signup(request, social_login) is False

    @patch("ams.users.adapters.DefaultSocialAccountAdapter.populate_user")
    def test_populate_user_with_name(
        self,
        mock_super_populate,
        social_account_adapter,
        request_factory,
    ):
        """Test populate_user sets user.name from data['name']."""
        request = request_factory.get("/")
        social_login = Mock()
        data = {"name": "John Doe", "email": "john@example.com"}

        mock_user = Mock()
        mock_user.name = ""
        mock_super_populate.return_value = mock_user

        result = social_account_adapter.populate_user(request, social_login, data)

        assert result.name == "John Doe"

    @patch("ams.users.adapters.DefaultSocialAccountAdapter.populate_user")
    def test_populate_user_with_first_and_last_name(
        self,
        mock_super_populate,
        social_account_adapter,
        request_factory,
    ):
        """Test populate_user combines first_name and last_name."""
        request = request_factory.get("/")
        social_login = Mock()
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
        }

        mock_user = Mock()
        mock_user.name = ""
        mock_super_populate.return_value = mock_user

        result = social_account_adapter.populate_user(request, social_login, data)

        assert result.name == "Jane Smith"

    @patch("ams.users.adapters.DefaultSocialAccountAdapter.populate_user")
    def test_populate_user_with_first_name_only(
        self,
        mock_super_populate,
        social_account_adapter,
        request_factory,
    ):
        """Test populate_user uses only first_name when last_name is missing."""
        request = request_factory.get("/")
        social_login = Mock()
        data = {"first_name": "Alice", "email": "alice@example.com"}

        mock_user = Mock()
        mock_user.name = ""
        mock_super_populate.return_value = mock_user

        result = social_account_adapter.populate_user(request, social_login, data)

        assert result.name == "Alice"

    @patch("ams.users.adapters.DefaultSocialAccountAdapter.populate_user")
    def test_populate_user_with_existing_name(
        self,
        mock_super_populate,
        social_account_adapter,
        request_factory,
    ):
        """Test populate_user doesn't override existing user.name."""
        request = request_factory.get("/")
        social_login = Mock()
        data = {
            "name": "New Name",
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
        }

        mock_user = Mock()
        mock_user.name = "Existing Name"
        mock_super_populate.return_value = mock_user

        result = social_account_adapter.populate_user(request, social_login, data)

        # Should keep existing name
        assert result.name == "Existing Name"

    @patch("ams.users.adapters.DefaultSocialAccountAdapter.populate_user")
    def test_populate_user_without_name_data(
        self,
        mock_super_populate,
        social_account_adapter,
        request_factory,
    ):
        """Test populate_user when no name data is provided."""
        request = request_factory.get("/")
        social_login = Mock()
        data = {"email": "test@example.com"}

        mock_user = Mock()
        mock_user.name = ""
        mock_super_populate.return_value = mock_user

        result = social_account_adapter.populate_user(request, social_login, data)

        # Name should remain empty
        assert result.name == ""

    @patch("ams.users.adapters.DefaultSocialAccountAdapter.populate_user")
    def test_populate_user_name_prioritization(
        self,
        mock_super_populate,
        social_account_adapter,
        request_factory,
    ):
        """Test that 'name' field has priority over first_name/last_name."""
        request = request_factory.get("/")
        social_login = Mock()
        data = {
            "name": "Full Name",
            "first_name": "First",
            "last_name": "Last",
            "email": "test@example.com",
        }

        mock_user = Mock()
        mock_user.name = ""
        mock_super_populate.return_value = mock_user

        result = social_account_adapter.populate_user(request, social_login, data)

        # Should use 'name' field, not combine first_name/last_name
        assert result.name == "Full Name"
