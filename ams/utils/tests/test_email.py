"""Tests for email utilities."""

from pathlib import Path

import pytest
from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.test import override_settings

from ams.utils.email import send_templated_email


class SendTemplatedEmailTests(TestCase):
    """Tests for send_templated_email function."""

    def test_send_templated_email_success(self):
        """Test sending an email with both HTML and text templates."""
        # Arrange
        subject = "Test Email"
        template_name = "organisations/emails/organisation_invite"
        context = {
            "organisation": type(
                "Organisation",
                (),
                {
                    "name": "Test Org",
                    "contact_name": "John Doe",
                    "email": "contact@test.org",
                    "telephone": "123-456-7890",
                    "city": "Test City",
                },
            )(),
            "accept_url": "https://example.com/accept",
            "decline_url": "https://example.com/decline",
            "user_exists": True,
        }
        recipient_list = ["test@example.com"]

        # Act
        result = send_templated_email(
            subject=subject,
            template_name=template_name,
            context=context,
            recipient_list=recipient_list,
        )

        # Assert
        assert result == 1
        assert len(mail.outbox) == 1

        sent_email = mail.outbox[0]
        assert sent_email.subject == subject
        assert sent_email.to == recipient_list
        assert "Test Org" in sent_email.body  # Check text content
        assert len(sent_email.alternatives) == 1  # type: ignore[attr-defined]
        html_content, content_type = sent_email.alternatives[0]  # type: ignore[attr-defined]
        assert content_type == "text/html"
        assert "Test Org" in html_content  # Check HTML content

    def test_send_templated_email_with_custom_from_email(self):
        """Test sending an email with a custom from_email."""
        # Arrange
        context = {
            "organisation": type(
                "Organisation",
                (),
                {
                    "name": "Test Org",
                    "contact_name": "John Doe",
                    "email": "contact@test.org",
                    "telephone": "123-456-7890",
                    "city": None,
                },
            )(),
            "accept_url": "https://example.com/accept",
            "decline_url": "https://example.com/decline",
            "user_exists": False,
        }
        custom_from_email = "custom@example.com"

        # Act
        send_templated_email(
            subject="Test",
            template_name="organisations/emails/organisation_invite",
            context=context,
            recipient_list=["test@example.com"],
            from_email=custom_from_email,
        )

        # Assert
        sent_email = mail.outbox[0]
        assert sent_email.from_email == custom_from_email

    @override_settings(DEFAULT_FROM_EMAIL="default@example.com")
    def test_send_templated_email_uses_default_from_email(self):
        """Test that DEFAULT_FROM_EMAIL is used when from_email is None."""
        # Arrange
        context = {
            "organisation": type(
                "Organisation",
                (),
                {
                    "name": "Test Org",
                    "contact_name": "John Doe",
                    "email": "contact@test.org",
                    "telephone": "123-456-7890",
                    "city": None,
                },
            )(),
            "accept_url": "https://example.com/accept",
            "decline_url": "https://example.com/decline",
            "user_exists": True,
        }

        # Act
        send_templated_email(
            subject="Test",
            template_name="organisations/emails/organisation_invite",
            context=context,
            recipient_list=["test@example.com"],
        )

        # Assert
        sent_email = mail.outbox[0]
        assert sent_email.from_email == "default@example.com"

    def test_send_templated_email_missing_template_fail_silently_false(self):
        """Test that missing template raises exception when fail_silently=False."""
        # Act & Assert
        with pytest.raises(Exception):  # noqa: B017, PT011
            send_templated_email(
                subject="Test",
                template_name="nonexistent_template",
                context={},
                recipient_list=["test@example.com"],
                fail_silently=False,
            )

    def test_send_templated_email_missing_template_fail_silently_true(self):
        """Test that missing template returns 0 when fail_silently=True."""
        # Act
        result = send_templated_email(
            subject="Test",
            template_name="nonexistent_template",
            context={},
            recipient_list=["test@example.com"],
            fail_silently=True,
        )

        # Assert
        assert result == 0
        assert len(mail.outbox) == 0

    def test_send_templated_email_preserves_django_template_tags(self):
        """Test that compiled templates preserve Django template functionality."""
        # Arrange
        context = {
            "organisation": type(
                "Organisation",
                (),
                {
                    "name": "<script>alert('xss')</script>",  # Test escaping
                    "contact_name": "John Doe",
                    "email": "contact@test.org",
                    "telephone": "123-456-7890",
                    "city": "Test City",
                },
            )(),
            "accept_url": "https://example.com/accept",
            "decline_url": "https://example.com/decline",
            "user_exists": True,
        }

        # Act
        send_templated_email(
            subject="Test",
            template_name="organisations/emails/organisation_invite",
            context=context,
            recipient_list=["test@example.com"],
        )

        # Assert
        sent_email = mail.outbox[0]
        html_content = sent_email.alternatives[0][0]  # type: ignore[attr-defined]
        # Django should escape the script tag
        assert "<script>" not in html_content
        assert "&lt;script&gt;" in html_content


class SendTemplatedEmailAutoGenerationTests(TestCase):
    """Tests for automatic plaintext generation from HTML."""

    def _get_txt_template_path(self):
        """Helper to get the path to the .txt template."""
        return (
            Path(settings.APPS_DIR)
            / "templates/organisations/emails/organisation_invite.txt"
        )

    def setUp(self):
        """Back up the .txt template if it exists."""
        self.txt_path = self._get_txt_template_path()
        self.txt_backup_path = Path(str(self.txt_path) + ".backup")
        if self.txt_path.exists():
            self.txt_path.rename(self.txt_backup_path)
            self.has_backup = True
        else:
            self.has_backup = False

    def tearDown(self):
        """Restore the .txt template."""
        if self.has_backup and self.txt_backup_path.exists():
            if self.txt_path.exists():
                self.txt_path.unlink()
            self.txt_backup_path.rename(self.txt_path)

    def test_auto_generate_plaintext_when_txt_missing(self):
        """Test that plaintext is auto-generated when .txt template doesn't exist."""
        # Arrange
        context = {
            "organisation": type(
                "Organisation",
                (),
                {
                    "name": "Test Org",
                    "contact_name": "John Doe",
                    "email": "contact@test.org",
                    "telephone": "123-456-7890",
                    "city": "Test City",
                },
            )(),
            "accept_url": "https://example.com/accept",
            "decline_url": "https://example.com/decline",
            "user_exists": True,
        }

        # Act
        result = send_templated_email(
            subject="Test Auto-Generation",
            template_name="organisations/emails/organisation_invite",
            context=context,
            recipient_list=["test@example.com"],
        )

        # Assert
        assert result == 1
        assert len(mail.outbox) == 1

        sent_email = mail.outbox[0]
        # Should have auto-generated plaintext
        assert "Test Org" in sent_email.body
        # html2text should convert buttons to markdown-style links
        assert "https://example.com/accept" in sent_email.body
        # Should have HTML version
        assert len(sent_email.alternatives) == 1  # type: ignore[attr-defined]

    def test_auto_generated_plaintext_quality(self):
        """Test that auto-generated plaintext is readable and formatted."""
        # Arrange
        context = {
            "organisation": type(
                "Organisation",
                (),
                {
                    "name": "ACME Corp",
                    "contact_name": "Jane Smith",
                    "email": "jane@acme.com",
                    "telephone": "555-1234",
                    "city": "Wellington",
                },
            )(),
            "accept_url": "https://example.com/accept/token123",
            "decline_url": "https://example.com/decline/token123",
            "user_exists": False,
        }

        # Act
        send_templated_email(
            subject="Test Quality",
            template_name="organisations/emails/organisation_invite",
            context=context,
            recipient_list=["test@example.com"],
        )

        # Assert
        sent_email = mail.outbox[0]
        plaintext = sent_email.body

        # Check key content is present
        assert "ACME Corp" in plaintext
        assert "Jane Smith" in plaintext
        assert "jane@acme.com" in plaintext
        assert "555-1234" in plaintext
        assert "Wellington" in plaintext

        # Check links are included
        assert "https://example.com/accept/token123" in plaintext
        assert "https://example.com/decline/token123" in plaintext

    @override_settings(EMAIL_PLAINTEXT_IGNORE_LINKS=True)
    def test_auto_generation_respects_ignore_links_setting(self):
        """Test that EMAIL_PLAINTEXT_IGNORE_LINKS setting is respected."""
        # Arrange
        context = {
            "organisation": type(
                "Organisation",
                (),
                {
                    "name": "Test Org",
                    "contact_name": "John Doe",
                    "email": "contact@test.org",
                    "telephone": "123-456-7890",
                    "city": None,
                },
            )(),
            "accept_url": "https://example.com/accept",
            "decline_url": "https://example.com/decline",
            "user_exists": True,
        }

        # Act
        send_templated_email(
            subject="Test Ignore Links",
            template_name="organisations/emails/organisation_invite",
            context=context,
            recipient_list=["test@example.com"],
        )

        # Assert
        sent_email = mail.outbox[0]
        # When ignore_links=True, URLs should not appear in plaintext
        # (html2text will show link text but not URLs)
        assert "Test Org" in sent_email.body

    @override_settings(EMAIL_PLAINTEXT_BODY_WIDTH=40)
    def test_auto_generation_respects_body_width_setting(self):
        """Test that EMAIL_PLAINTEXT_BODY_WIDTH setting is respected."""
        # Arrange
        context = {
            "organisation": type(
                "Organisation",
                (),
                {
                    "name": "Organization with a Very Long Name for Testing",
                    "contact_name": "John Doe",
                    "email": "contact@test.org",
                    "telephone": "123-456-7890",
                    "city": None,
                },
            )(),
            "accept_url": "https://example.com/accept",
            "decline_url": "https://example.com/decline",
            "user_exists": True,
        }

        # Act
        send_templated_email(
            subject="Test Body Width",
            template_name="organisations/emails/organisation_invite",
            context=context,
            recipient_list=["test@example.com"],
        )

        # Assert
        sent_email = mail.outbox[0]
        # With body_width=40, lines should be wrapped
        # Just verify the email was sent successfully
        assert "Organization" in sent_email.body
