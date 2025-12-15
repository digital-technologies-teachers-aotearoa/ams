"""Tests for the fetch_invoice_updates management command."""

from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command

from ams.billing.providers.mock.service import MockBillingService
from ams.billing.providers.xero.service import XeroBillingService


@pytest.mark.django_db
class TestFetchInvoiceUpdatesCommand:
    """Test suite for fetch_invoice_updates management command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.stdout = StringIO()
        self.stderr = StringIO()

    def test_command_with_no_billing_service_configured(self, settings):
        """Test command when no billing service is configured."""
        settings.BILLING_SERVICE_CLASS = None

        call_command(
            "fetch_invoice_updates",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        output = self.stdout.getvalue()
        assert "No billing service configured." in output

    def test_command_with_xero_billing_service(self, settings):
        """Test command with Xero billing service configured."""
        settings.BILLING_SERVICE_CLASS = "ams.billing.providers.xero.XeroBillingService"

        with patch(
            "ams.billing.management.commands.fetch_invoice_updates.fetch_updated_invoice_details",
        ) as mock_fetch:
            mock_fetch.return_value = {
                "updated_count": 0,
                "invoice_numbers": [],
                "invoice_ids": [],
            }
            call_command(
                "fetch_invoice_updates",
                stdout=self.stdout,
                stderr=self.stderr,
            )

            output = self.stdout.getvalue()
            assert "Fetching updates to invoices for Xero billing..." in output
            assert "No invoices needed updating" in output
            assert "Done" in output
            mock_fetch.assert_called_once_with(raise_exception=True)

    def test_command_with_mock_xero_billing_service(self, settings):
        """Test command with MockXeroBillingService configured.

        MockXeroBillingService is checked before XeroBillingService in the command,
        so it will take the mock billing path.
        """
        settings.BILLING_SERVICE_CLASS = (
            "ams.billing.providers.xero.MockXeroBillingService"
        )

        call_command(
            "fetch_invoice_updates",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        output = self.stdout.getvalue()
        assert "No invoice updates to fetch with mock billing." in output
        assert "Done" in output

    def test_command_with_mock_billing_service(self, settings):
        """Test command with MockBillingService configured."""
        settings.BILLING_SERVICE_CLASS = "ams.billing.providers.mock.MockBillingService"

        call_command(
            "fetch_invoice_updates",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        output = self.stdout.getvalue()
        assert "No invoice updates to fetch with mock billing." in output
        assert "Done" in output

    def test_command_with_unknown_billing_service(self, settings):
        """Test command with unknown billing service type."""

        # Create a fake billing service class
        class UnknownBillingService:
            pass

        with patch(
            "ams.billing.management.commands.fetch_invoice_updates.get_billing_service",
        ) as mock_get_service:
            mock_get_service.return_value = UnknownBillingService()

            call_command(
                "fetch_invoice_updates",
                stdout=self.stdout,
                stderr=self.stderr,
            )

            output = self.stdout.getvalue()
            assert "Unknown billing service configured." in output

    @patch(
        "ams.billing.management.commands.fetch_invoice_updates.fetch_updated_invoice_details",
    )
    def test_command_propagates_exceptions_from_fetch(
        self,
        mock_fetch,
        settings,
    ):
        """Test that exceptions from fetch_updated_invoice_details are propagated."""
        settings.BILLING_SERVICE_CLASS = "ams.billing.providers.xero.XeroBillingService"
        mock_fetch.side_effect = Exception("Test exception")

        with pytest.raises(Exception, match="Test exception"):
            call_command(
                "fetch_invoice_updates",
                stdout=self.stdout,
                stderr=self.stderr,
            )

    def test_command_with_xero_service_instance_check(self, settings):
        """Test that command correctly identifies XeroBillingService instances."""
        settings.BILLING_SERVICE_CLASS = "ams.billing.providers.xero.XeroBillingService"

        with patch(
            "ams.billing.management.commands.fetch_invoice_updates.get_billing_service",
        ) as mock_get_service:
            mock_service = XeroBillingService()
            mock_get_service.return_value = mock_service

            with patch(
                "ams.billing.management.commands.fetch_invoice_updates.fetch_updated_invoice_details",
            ) as mock_fetch:
                mock_fetch.return_value = {
                    "updated_count": 0,
                    "invoice_numbers": [],
                    "invoice_ids": [],
                }
                call_command(
                    "fetch_invoice_updates",
                    stdout=self.stdout,
                    stderr=self.stderr,
                )

                output = self.stdout.getvalue()
                assert "Fetching updates to invoices for Xero billing..." in output
                mock_fetch.assert_called_once()

    def test_command_with_mock_service_instance_check(self, settings):
        """Test that command correctly identifies MockBillingService instances."""
        settings.BILLING_SERVICE_CLASS = "ams.billing.providers.mock.MockBillingService"

        with patch(
            "ams.billing.management.commands.fetch_invoice_updates.get_billing_service",
        ) as mock_get_service:
            mock_service = MockBillingService()
            mock_get_service.return_value = mock_service

            call_command(
                "fetch_invoice_updates",
                stdout=self.stdout,
                stderr=self.stderr,
            )

            output = self.stdout.getvalue()
            assert "No invoice updates to fetch with mock billing." in output

    def test_command_with_updated_invoices_output(self, settings):
        """Test command displays updated invoice information."""
        settings.BILLING_SERVICE_CLASS = "ams.billing.providers.xero.XeroBillingService"

        with patch(
            "ams.billing.management.commands.fetch_invoice_updates.fetch_updated_invoice_details",
        ) as mock_fetch:
            mock_fetch.return_value = {
                "updated_count": 3,
                "invoice_numbers": ["INV-001", "INV-002", "INV-003"],
                "invoice_ids": [1, 2, 3],
            }
            call_command(
                "fetch_invoice_updates",
                stdout=self.stdout,
                stderr=self.stderr,
            )

            output = self.stdout.getvalue()
            assert "Fetching updates to invoices for Xero billing..." in output
            assert "Updated 3 invoice(s):" in output
            assert "INV-001" in output
            assert "INV-002" in output
            assert "INV-003" in output
            assert "Done" in output

    def test_command_with_single_invoice_update(self, settings):
        """Test command displays single invoice update correctly."""
        settings.BILLING_SERVICE_CLASS = "ams.billing.providers.xero.XeroBillingService"

        with patch(
            "ams.billing.management.commands.fetch_invoice_updates.fetch_updated_invoice_details",
        ) as mock_fetch:
            mock_fetch.return_value = {
                "updated_count": 1,
                "invoice_numbers": ["INV-123"],
                "invoice_ids": [1],
            }
            call_command(
                "fetch_invoice_updates",
                stdout=self.stdout,
                stderr=self.stderr,
            )

            output = self.stdout.getvalue()
            assert "Updated 1 invoice(s):" in output
            assert "INV-123" in output
