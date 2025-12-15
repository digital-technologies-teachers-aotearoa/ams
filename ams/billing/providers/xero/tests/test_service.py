"""Tests for Xero billing service."""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from xero_python.accounting import Invoice as XeroInvoiceModel

from ams.billing.providers.xero.models import XeroContact
from ams.billing.providers.xero.service import MockXeroBillingService
from ams.billing.providers.xero.service import XeroBillingService

pytestmark = pytest.mark.django_db


class TestXeroBillingServiceInitialization:
    """Tests for XeroBillingService initialization."""

    def test_service_initializes_with_correct_settings(self, xero_settings):
        """Test that service initializes with configured settings."""
        with patch("ams.billing.providers.xero.service.ApiClient") as mock_client:
            service = XeroBillingService()

            assert service.xero_token is None
            mock_client.assert_called_once()

            # Verify Configuration was created with correct parameters
            call_args = mock_client.call_args
            config = call_args[0][0]
            assert config.debug is False

    def test_token_getter_returns_none_initially(
        self,
        xero_settings,
        mock_xero_api_client,
    ):
        """Test that token getter returns None when no token is set."""
        service = XeroBillingService()
        assert service.get_xero_token() is None

    def test_token_setter_and_getter(self, xero_service):
        """Test token setter and getter work correctly."""
        xero_service.set_xero_token("test-access-token")
        assert xero_service.get_xero_token() == "test-access-token"


class TestXeroBillingServiceContactManagement:
    """Tests for contact creation and updates."""

    @patch("ams.billing.providers.xero.service.AccountingApi")
    def test_create_xero_contact(
        self,
        mock_accounting_api_class,
        xero_service,
        xero_contact_response,
        xero_settings,
    ):
        """Test creating a new contact in Xero."""
        mock_api = Mock()
        mock_api.create_contacts.return_value = xero_contact_response
        mock_accounting_api_class.return_value = mock_api

        contact_params = {
            "name": "Test User (1)",
            "account_number": "1",
            "email_address": "test@example.com",
        }

        contact_id = xero_service._create_xero_contact(contact_params)  # noqa: SLF001

        assert contact_id == "test-contact-id-123"
        mock_api.create_contacts.assert_called_once()

        # Verify the call was made with correct tenant ID
        call_args = mock_api.create_contacts.call_args
        assert call_args[0][0] == xero_settings.XERO_TENANT_ID

    @patch("ams.billing.providers.xero.service.AccountingApi")
    def test_update_xero_contact(
        self,
        mock_accounting_api_class,
        xero_service,
        xero_settings,
    ):
        """Test updating an existing contact in Xero."""
        mock_api = Mock()
        mock_accounting_api_class.return_value = mock_api

        contact_id = "existing-contact-id"
        contact_params = {
            "name": "Updated User (1)",
            "email_address": "updated@example.com",
        }

        xero_service._update_xero_contact(contact_id, contact_params)  # noqa: SLF001

        mock_api.update_contact.assert_called_once()
        call_args = mock_api.update_contact.call_args
        assert call_args[0][0] == xero_settings.XERO_TENANT_ID
        assert call_args[0][1] == contact_id

    def test_xero_contact_name_includes_account_id(self, xero_service):
        """Test that contact names include account ID for uniqueness."""
        name = xero_service._xero_contact_name(123, "John Doe")  # noqa: SLF001
        assert name == "John Doe (123)"

    @patch("ams.billing.providers.xero.service.AccountingApi")
    def test_update_user_billing_details_creates_new_contact(
        self,
        mock_accounting_api_class,
        xero_service,
        user,
        account_user,
        xero_contact_response,
    ):
        """Test updating user billing details creates contact if not exists."""
        mock_api = Mock()
        mock_api.create_contacts.return_value = xero_contact_response
        mock_accounting_api_class.return_value = mock_api

        with patch.object(xero_service, "_get_authentication_token"):
            xero_service.update_user_billing_details(user)

        # Verify XeroContact was created in database
        xero_contact = XeroContact.objects.get(account=account_user)
        assert xero_contact.contact_id == "test-contact-id-123"

    @patch("ams.billing.providers.xero.service.AccountingApi")
    def test_update_user_billing_details_updates_existing_contact(
        self,
        mock_accounting_api_class,
        xero_service,
        user,
        xero_contact_model,
    ):
        """Test updating user billing details when contact already exists."""
        mock_api = Mock()
        mock_accounting_api_class.return_value = mock_api

        with patch.object(xero_service, "_get_authentication_token"):
            xero_service.update_user_billing_details(user)

        # Should call update, not create
        mock_api.update_contact.assert_called_once()
        mock_api.create_contacts.assert_not_called()

    @patch("ams.billing.providers.xero.service.AccountingApi")
    def test_update_organisation_billing_details(
        self,
        mock_accounting_api_class,
        xero_service,
        organisation,
        account_organisation,
        xero_contact_response,
    ):
        """Test updating organisation billing details."""
        mock_api = Mock()
        mock_api.create_contacts.return_value = xero_contact_response
        mock_accounting_api_class.return_value = mock_api

        with patch.object(xero_service, "_get_authentication_token"):
            xero_service.update_organisation_billing_details(organisation)

        # Verify contact was created
        xero_contact = XeroContact.objects.get(account=account_organisation)
        assert xero_contact.contact_id == "test-contact-id-123"


class TestXeroBillingServiceInvoiceManagement:
    """Tests for invoice creation and management."""

    @patch("ams.billing.providers.xero.service.AccountingApi")
    def test_create_invoice(  # noqa: PLR0913
        self,
        mock_accounting_api_class,
        xero_service,
        account_user,
        xero_contact_model,
        xero_invoice_response,
        xero_settings,
    ):
        """Test creating an invoice in Xero."""
        mock_api = Mock()
        mock_api.create_invoices.return_value = xero_invoice_response
        mock_accounting_api_class.return_value = mock_api

        with patch.object(xero_service, "_get_authentication_token"):
            invoice = xero_service.create_invoice(
                account=account_user,
                date=date(2024, 1, 15),
                due_date=date(2024, 2, 15),
                line_items=[
                    {
                        "description": "Membership Fee",
                        "quantity": 1,
                        "unit_amount": Decimal("100.00"),
                    },
                ],
            )

        # Verify invoice was created in database
        assert invoice.account == account_user
        assert invoice.billing_service_invoice_id == "test-invoice-id-123"
        assert invoice.invoice_number == "INV-001"
        assert invoice.amount == Decimal("100.0")
        assert invoice.due == Decimal("100.0")
        assert invoice.paid == Decimal("0.0")

    @patch("ams.billing.providers.xero.service.AccountingApi")
    def test_create_invoice_with_multiple_line_items(
        self,
        mock_accounting_api_class,
        xero_service,
        account_user,
        xero_contact_model,
        xero_settings,
    ):
        """Test creating invoice with multiple line items."""
        xero_invoice = XeroInvoiceModel(
            invoice_id="multi-line-invoice",
            invoice_number="INV-002",
            date="2024-01-15",
            due_date="2024-02-15",
            total=250.0,
            amount_due=250.0,
            amount_paid=0.0,
        )
        response = Mock()
        response.invoices = [xero_invoice]

        mock_api = Mock()
        mock_api.create_invoices.return_value = response
        mock_accounting_api_class.return_value = mock_api

        line_items = [
            {
                "description": "Membership Fee",
                "quantity": 1,
                "unit_amount": Decimal("100.00"),
            },
            {
                "description": "Late Fee",
                "quantity": 1,
                "unit_amount": Decimal("50.00"),
            },
            {
                "description": "Processing Fee",
                "quantity": 2,
                "unit_amount": Decimal("50.00"),
            },
        ]

        with patch.object(xero_service, "_get_authentication_token"):
            invoice = xero_service.create_invoice(
                account=account_user,
                date=date(2024, 1, 15),
                due_date=date(2024, 2, 15),
                line_items=line_items,
            )

        assert invoice.amount == Decimal("250.0")

    @patch("ams.billing.providers.xero.service.AccountingApi")
    def test_email_invoice(
        self,
        mock_accounting_api_class,
        xero_service,
        invoice_user,
        xero_settings,
    ):
        """Test emailing an invoice via Xero."""
        mock_api = Mock()
        mock_accounting_api_class.return_value = mock_api

        invoice_user.billing_service_invoice_id = "test-invoice-123"
        invoice_user.save()

        with patch.object(xero_service, "_get_authentication_token"):
            xero_service.email_invoice(invoice_user)

        mock_api.email_invoice.assert_called_once()
        call_args = mock_api.email_invoice.call_args
        assert call_args[0][0] == xero_settings.XERO_TENANT_ID
        assert call_args[0][1] == "test-invoice-123"

    @patch("ams.billing.providers.xero.service.AccountingApi")
    def test_update_invoices(
        self,
        mock_accounting_api_class,
        xero_service,
        invoice_user,
        xero_settings,
    ):
        """Test updating invoice details from Xero."""
        invoice_user.billing_service_invoice_id = "test-invoice-123"
        invoice_user.update_needed = True
        invoice_user.save()

        # Mock Xero response with updated data
        xero_invoice = XeroInvoiceModel(
            invoice_id="test-invoice-123",
            invoice_number="INV-001",
            date="2024-01-15",
            due_date="2024-02-15",
            total=100.0,
            amount_due=50.0,  # Partially paid
            amount_paid=50.0,
            fully_paid_on_date="2024-01-20",
        )
        response = Mock()
        response.invoices = [xero_invoice]

        mock_api = Mock()
        mock_api.get_invoices.return_value = response
        mock_accounting_api_class.return_value = mock_api

        with patch.object(xero_service, "_get_authentication_token"):
            xero_service.update_invoices(["test-invoice-123"])

        # Verify invoice was updated in database
        invoice_user.refresh_from_db()
        assert invoice_user.paid == Decimal("50.0")
        assert invoice_user.due == Decimal("50.0")
        assert invoice_user.paid_date is not None
        assert invoice_user.update_needed is False


class TestXeroBillingServiceAuthentication:
    """Tests for authentication and token management."""

    def test_get_client_credentials_token(self, xero_service):
        """Test getting client credentials token."""
        with patch.object(
            xero_service.api_client,
            "get_client_credentials_token",
        ) as mock_token:
            xero_service._get_client_credentials_token()  # noqa: SLF001
            mock_token.assert_called_once()

    def test_get_authentication_token_gets_token_when_none_exists(self, xero_service):
        """Test that token is acquired when no token exists."""
        xero_service.set_xero_token(None)

        with patch.object(
            xero_service,
            "_get_client_credentials_token",
        ) as mock_get_token:
            xero_service._get_authentication_token()  # noqa: SLF001

        mock_get_token.assert_called_once()

    def test_get_authentication_token_skips_when_token_exists(self, xero_service):
        """Test that authentication is skipped when token exists."""
        xero_service.set_xero_token("existing-token")

        with patch.object(
            xero_service,
            "_get_client_credentials_token",
        ) as mock_get_token:
            xero_service._get_authentication_token()  # noqa: SLF001

        mock_get_token.assert_not_called()

    @patch("ams.billing.providers.xero.service.IdentityApi")
    def test_get_connections(
        self,
        mock_identity_api_class,
        xero_service,
        xero_connections_response,
    ):
        """Test getting Xero connections."""
        mock_api = Mock()
        mock_api.get_connections.return_value = xero_connections_response
        mock_identity_api_class.return_value = mock_api

        connections = xero_service._get_connections()  # noqa: SLF001

        assert len(connections) == 1
        assert connections[0].tenant_id == "test-tenant-id"


class TestMockXeroBillingService:
    """Tests for MockXeroBillingService."""

    def test_mock_service_creates_contact(self, xero_settings):
        """Test that mock service returns mock contact ID."""
        service = MockXeroBillingService()
        contact_id = service._create_xero_contact({"name": "Test"})  # noqa: SLF001
        assert contact_id == "mock-xero-contact-id"

    def test_mock_service_updates_contact(self, xero_settings):
        """Test that mock service handles contact updates."""
        service = MockXeroBillingService()
        # Should not raise any errors
        service._update_xero_contact("contact-id", {"name": "Updated"})  # noqa: SLF001

    def test_mock_service_creates_invoice(self, xero_settings, account_user):
        """Test that mock service creates invoices locally."""
        service = MockXeroBillingService()
        service.set_xero_token("mock-token")

        # Need to create XeroContact first
        XeroContact.objects.create(
            account=account_user,
            contact_id="mock-xero-contact-id",
        )

        invoice = service.create_invoice(
            account=account_user,
            date=date(2024, 1, 15),
            due_date=date(2024, 2, 15),
            line_items=[
                {
                    "description": "Test Item",
                    "quantity": 2,
                    "unit_amount": Decimal("50.00"),
                },
            ],
        )

        assert invoice.account == account_user
        assert invoice.amount == Decimal("100.00")
        assert invoice.invoice_number == "INV-1234"

    def test_mock_service_email_invoice(self, xero_settings, invoice_user):
        """Test that mock service handles email requests."""
        service = MockXeroBillingService()
        # Should not raise any errors
        service.email_invoice(invoice_user)

    def test_mock_service_update_invoices(self, xero_settings):
        """Test that mock service handles invoice updates."""
        service = MockXeroBillingService()
        # Should return empty list
        invoices = service._get_xero_invoices(["invoice-id"])  # noqa: SLF001
        assert invoices == []

    def test_mock_service_get_connections(self, xero_settings):
        """Test that mock service returns empty connections."""
        service = MockXeroBillingService()
        connections = service._get_connections()  # noqa: SLF001
        assert connections == []
