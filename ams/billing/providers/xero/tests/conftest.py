"""Pytest fixtures for Xero billing provider tests."""

from unittest.mock import Mock
from unittest.mock import patch

import pytest
from xero_python.accounting import Contact as XeroContactAPI
from xero_python.accounting import Invoice as XeroInvoice
from xero_python.identity import Connection

from ams.billing.providers.xero.models import XeroContact
from ams.billing.providers.xero.service import XeroBillingService


@pytest.fixture
def xero_settings(settings):
    """Configure Xero settings for testing."""
    settings.XERO_CLIENT_ID = "test-client-id"
    settings.XERO_CLIENT_SECRET = "test-client-secret"  # noqa: S105
    settings.XERO_TENANT_ID = "test-tenant-id"
    settings.XERO_WEBHOOK_KEY = "test-webhook-key"
    settings.XERO_ACCOUNT_CODE = "200"
    settings.XERO_AMOUNT_TYPE = "INCLUSIVE"
    settings.XERO_CURRENCY_CODE = "NZD"
    settings.DEBUG = False
    return settings


@pytest.fixture
def mock_xero_api_client():
    """Mock Xero API client."""
    with patch("ams.billing.providers.xero.service.ApiClient") as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_accounting_api():
    """Mock Xero AccountingApi."""
    with patch("ams.billing.providers.xero.service.AccountingApi") as mock_api:
        mock_instance = Mock()
        mock_api.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_identity_api():
    """Mock Xero IdentityApi."""
    with patch("ams.billing.providers.xero.service.IdentityApi") as mock_api:
        mock_instance = Mock()
        mock_api.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def xero_service(xero_settings, mock_xero_api_client):
    """Create XeroBillingService instance with mocked dependencies."""
    service = XeroBillingService()
    # Set a test token
    service.set_xero_token("test-token-value")
    return service


@pytest.fixture
def xero_contact_response():
    """Mock Xero Contact API response."""
    contact = XeroContactAPI(
        contact_id="test-contact-id-123",
        name="Test User (1)",
        email_address="test@example.com",
        account_number="1",
    )
    response = Mock()
    response.contacts = [contact]
    return response


@pytest.fixture
def xero_invoice_response():
    """Mock Xero Invoice API response."""
    invoice = XeroInvoice(
        invoice_id="test-invoice-id-123",
        invoice_number="INV-001",
        type="ACCREC",
        date="2024-01-15",
        due_date="2024-02-15",
        total=100.0,
        amount_due=100.0,
        amount_paid=0.0,
        fully_paid_on_date=None,
    )
    response = Mock()
    response.invoices = [invoice]
    return response


@pytest.fixture
def xero_connections_response():
    """Mock Xero connections response."""
    connection = Connection(
        id="test-connection-id",
        tenant_id="test-tenant-id",
        tenant_type="ORGANISATION",
        tenant_name="Test Organisation",
    )
    return [connection]


@pytest.fixture
def xero_contact_model(account_user):
    """Create a XeroContact database record."""
    return XeroContact.objects.create(
        account=account_user,
        contact_id="test-contact-id-456",
    )


@pytest.fixture
def webhook_payload():
    """Sample Xero webhook payload."""
    return {
        "events": [
            {
                "resourceUrl": "https://api.xero.com/api.xro/2.0/Invoices/test-invoice-id",
                "resourceId": "test-invoice-id-123",
                "eventDateUtc": "2024-01-15T12:00:00.000",
                "eventType": "UPDATE",
                "eventCategory": "INVOICE",
                "tenantId": "test-tenant-id",
                "tenantType": "ORGANISATION",
            },
        ],
        "lastEventSequence": 1,
        "firstEventSequence": 1,
        "entropy": "test-entropy-string",
    }
