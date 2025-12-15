import json
from contextlib import suppress
from typing import TYPE_CHECKING
from typing import Any

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import HttpResponse
from xero_python.accounting import AccountingApi
from xero_python.accounting import Contact
from xero_python.accounting import Contacts
from xero_python.accounting import CurrencyCode
from xero_python.accounting import Invoice as AccountingInvoice
from xero_python.accounting import Invoices
from xero_python.accounting import LineAmountTypes
from xero_python.accounting import LineItem
from xero_python.accounting import RequestEmpty
from xero_python.api_client import ApiClient
from xero_python.api_client.configuration import Configuration
from xero_python.api_client.oauth2 import OAuth2Token
from xero_python.api_client.serializer import serialize
from xero_python.identity import Connection
from xero_python.identity import IdentityApi

from ams.billing.models import Account
from ams.billing.models import Invoice
from ams.billing.providers.xero.models import XeroContact
from ams.billing.providers.xero.rate_limiting import handle_rate_limit
from ams.billing.services import BillingService
from ams.memberships.models import Organisation

if TYPE_CHECKING:  # pragma: no cover
    from datetime import date


class XeroBillingService(BillingService):
    """Xero accounting system integration for billing services."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the Xero billing service with OAuth2 configuration.

        Sets up the Xero API client with OAuth2 credentials from Django settings
        and configures token getter/setter callbacks for authentication management.
        """
        super().__init__(*args, **kwargs)

        self.xero_token: str | None = None

        self.api_client = ApiClient(
            Configuration(
                debug=settings.XERO_DEBUG,
                oauth2_token=OAuth2Token(
                    client_id=settings.XERO_CLIENT_ID,
                    client_secret=settings.XERO_CLIENT_SECRET,
                ),
            ),
            pool_threads=1,
            oauth2_token_getter=self.get_xero_token,
            oauth2_token_saver=self.set_xero_token,
        )

    def get_xero_token(self) -> str | None:
        """Retrieve the current Xero OAuth2 access token.

        Returns:
            The current access token string, or None if not set.
        """
        return self.xero_token

    def set_xero_token(self, token: str) -> None:
        """Store the Xero OAuth2 access token.

        Args:
            token: The OAuth2 access token string to store.
        """
        self.xero_token = token

    def _debug_response(self, data: Any) -> HttpResponse:
        """Create a JSON HTTP response for debugging Xero API data.

        Args:
            data: Any Xero API response object to serialize.

        Returns:
            HttpResponse containing the serialized JSON data.
        """
        return HttpResponse(
            json.dumps(serialize(data)),
            content_type="application/json",
        )

    def _get_client_credentials_token(self) -> None:
        """Obtain a client credentials token from Xero OAuth2.

        Requests a new access token using the OAuth2 client credentials flow.
        The token is automatically stored via the set_xero_token callback.
        """
        self.api_client.get_client_credentials_token()

    def _get_authentication_token(self) -> None:
        """Ensure a valid authentication token is available.

        If no token is currently set, requests a new client credentials token
        from Xero. Should be called before any Xero API operations.
        """
        if not self.get_xero_token():
            self._get_client_credentials_token()

    def _get_connections(self) -> list[Connection]:
        """Retrieve all Xero tenant connections for the authenticated app.

        Returns:
            List of Connection objects representing authorized Xero tenants.
        """
        api_instance = IdentityApi(self.api_client)
        connections: list[Connection] = api_instance.get_connections()
        return connections

    @handle_rate_limit()
    def _create_xero_contact(self, contact_params: dict[str, Any]) -> str:
        """Create a new contact in Xero.

        Args:
            contact_params: Dictionary of contact attributes (name, email_address,
                account_number, etc.) to pass to the Xero Contact constructor.

        Returns:
            The Xero-generated contact ID string.
        """
        api_instance = AccountingApi(self.api_client)

        contact = Contact(**contact_params)
        contacts = Contacts(contacts=[contact])

        api_response = api_instance.create_contacts(settings.XERO_TENANT_ID, contacts)

        contact_id: str = api_response.contacts[0].contact_id
        return contact_id

    @handle_rate_limit()
    def _update_xero_contact(
        self,
        contact_id: str,
        contact_params: dict[str, Any],
    ) -> None:
        """Update an existing contact in Xero.

        Args:
            contact_id: The Xero contact ID to update.
            contact_params: Dictionary of contact attributes to update.
        """
        api_instance = AccountingApi(self.api_client)

        contact = Contact(**contact_params)
        contacts = Contacts(contacts=[contact])

        api_instance.update_contact(settings.XERO_TENANT_ID, contact_id, contacts)

    @handle_rate_limit()
    def _create_xero_invoice(
        self,
        contact_id: str,
        invoice_details: dict[str, Any],
        line_item_details: list[dict[str, Any]],
    ) -> AccountingInvoice:
        """Create a new invoice in Xero.

        Args:
            contact_id: The Xero contact ID to bill.
            invoice_details: Dictionary of invoice attributes (type, date, due_date,
                reference, currency_code, status, line_amount_types).
            line_item_details: List of dictionaries containing line item attributes
                (description, unit_amount, quantity, account_code).

        Returns:
            The created AccountingInvoice object from Xero's API response.
        """
        api_instance = AccountingApi(self.api_client)

        contact = Contact(contact_id=contact_id)
        line_items = [LineItem(**item_details) for item_details in line_item_details]

        invoice = AccountingInvoice(
            contact=contact,
            line_items=line_items,
            **invoice_details,
        )
        invoices = Invoices(invoices=[invoice])

        api_response = api_instance.create_invoices(settings.XERO_TENANT_ID, invoices)

        response_invoice: AccountingInvoice = api_response.invoices[0]
        return response_invoice

    @handle_rate_limit()
    def _email_invoice(self, billing_service_invoice_id: str) -> None:
        """Send an invoice email via Xero.

        Args:
            billing_service_invoice_id: The Xero invoice ID to email.
        """
        api_instance = AccountingApi(self.api_client)
        api_instance.email_invoice(
            settings.XERO_TENANT_ID,
            billing_service_invoice_id,
            RequestEmpty(),
        )

    @handle_rate_limit()
    def _get_xero_invoices(
        self,
        billing_service_invoice_ids: list[str],
    ) -> list[AccountingInvoice]:
        """Retrieve invoices from Xero by their IDs.

        Args:
            billing_service_invoice_ids: List of Xero invoice IDs to retrieve.

        Returns:
            List of AccountingInvoice objects from Xero.
        """
        api_instance = AccountingApi(self.api_client)
        api_response = api_instance.get_invoices(
            settings.XERO_TENANT_ID,
            i_ds=billing_service_invoice_ids,
        )
        invoices: list[AccountingInvoice] = api_response.invoices
        return invoices

    @handle_rate_limit()
    def _get_online_invoice_url(self, billing_service_invoice_id: str) -> str:
        """Get the online invoice URL from Xero.

        Args:
            billing_service_invoice_id: The Xero invoice ID.

        Returns:
            The online invoice URL from Xero.
        """
        api_instance = AccountingApi(self.api_client)
        api_response = api_instance.get_online_invoice(
            settings.XERO_TENANT_ID,
            billing_service_invoice_id,
        )
        return api_response.online_invoices[0].online_invoice_url

    def get_invoice_url(self, invoice: Invoice) -> str | None:
        """Get the online invoice URL for viewing.

        Fetches the customer-facing online invoice URL from Xero that can be
        used to view and pay the invoice.

        Args:
            invoice: The Invoice to get the URL for.
                     Must have a billing_service_invoice_id.

        Returns:
            The online invoice URL, or None if the invoice doesn't have
            a billing_service_invoice_id.
        """
        if not invoice.billing_service_invoice_id:
            return None
        self._get_authentication_token()
        return self._get_online_invoice_url(invoice.billing_service_invoice_id)

    def _xero_contact_name(self, account_id: int, name: str) -> str:
        """Generate a unique Xero contact name by appending the account ID.

        Xero requires contact names to be unique. This method ensures uniqueness
        by appending the account ID in parentheses to the contact's display name.

        Args:
            account_id: The AMS billing Account ID.
            name: The contact's display name (user full name or organization name).

        Returns:
            Formatted contact name string in the format "Name (account_id)".
        """
        return f"{name} ({account_id})"

    def update_user_billing_details(self, user: User) -> None:
        """Update or create a Xero contact for a user's billing account.

        Synchronizes the user's details (name, email, account number) with Xero.
        If a Xero contact exists for the user's account, it is updated; otherwise,
        a new contact is created.

        Args:
            user: The Django User whose billing details should be synchronized.
        """
        contact_details = {
            "name": self._xero_contact_name(user.account.pk, user.get_full_name()),
            "account_number": str(user.account.id),
            "email_address": user.email,
        }
        return self.update_account_billing_details(user.account, contact_details)

    def update_organisation_billing_details(self, organisation: Organisation) -> None:
        """Update or create a Xero contact for an organisation's billing account.

        Synchronizes the organisation's details (name, email, account number) with Xero.
        If a Xero contact exists for the organisation's account, it is updated;
        otherwise, a new contact is created.

        Args:
            organisation: The Organisation whose billing details should be synchronized.
        """
        contact_details = {
            "name": self._xero_contact_name(organisation.account.pk, organisation.name),
            "account_number": str(organisation.account.id),
            "email_address": organisation.email,
        }
        return self.update_account_billing_details(
            organisation.account,
            contact_details,
        )

    def update_account_billing_details(
        self,
        account: Account,
        contact_details: dict[str, Any],
    ) -> None:
        """Update or create a Xero contact for a billing account.

        Ensures authentication, then either updates an existing Xero contact or
        creates a new one. If creating, also stores the new XeroContact mapping
        in the database.

        Args:
            account: The billing Account to update in Xero.
            contact_details: Dictionary of contact attributes (name, email_address,
                account_number, etc.) to synchronize with Xero.
        """
        contact_id: str | None = None

        with suppress(ObjectDoesNotExist):
            contact_id = account.xero_contact.contact_id

        self._get_authentication_token()

        if contact_id:
            self._update_xero_contact(contact_id, contact_details)
        else:
            contact_id = self._create_xero_contact(contact_details)
            XeroContact.objects.create(account=account, contact_id=contact_id)

    def create_invoice(
        self,
        account: Account,
        date: "date",
        due_date: "date",
        line_items: list[dict[str, Any]],
    ) -> Invoice:
        """Create a new invoice in Xero and store it locally.

        Creates an ACCREC (accounts receivable) invoice in Xero for the specified
        account with the given line items. The invoice is created in AUTHORISED status.
        A corresponding Invoice record is created in the local database with details
        from the Xero response.

        Args:
            account: The billing Account to invoice, with an associated XeroContact.
            date: The invoice issue date.
            due_date: The invoice due date.
            line_items: List of dictionaries with keys 'description', 'unit_amount',
                and 'quantity' for each line item on the invoice.

        Returns:
            The newly created Invoice model instance.
        """
        contact_id = account.xero_contact.contact_id

        amount_type = LineAmountTypes[settings.XERO_AMOUNT_TYPE]
        account_code = settings.XERO_ACCOUNT_CODE
        currency_code = CurrencyCode[settings.XERO_CURRENCY_CODE]

        line_items = [
            {
                "description": line_item["description"],
                "unit_amount": line_item["unit_amount"],
                "quantity": line_item["quantity"],
                "account_code": account_code,
            }
            for line_item in line_items
        ]

        invoice_details = {
            "type": "ACCREC",
            "date": date,
            "due_date": due_date,
            "reference": str(account.pk),
            "currency_code": currency_code,
            "status": "AUTHORISED",
            "line_amount_types": amount_type,
        }

        accounting_invoice = self._create_xero_invoice(
            contact_id,
            invoice_details,
            line_items,
        )

        invoice: Invoice = Invoice.objects.create(
            account=account,
            billing_service_invoice_id=accounting_invoice.invoice_id,
            invoice_number=accounting_invoice.invoice_number,
            issue_date=accounting_invoice.date,
            due_date=accounting_invoice.due_date,
            amount=accounting_invoice.total,
            due=accounting_invoice.amount_due,
            paid=accounting_invoice.amount_paid,
        )

        return invoice

    def email_invoice(self, invoice: Invoice) -> None:
        """Send an invoice email via Xero to the contact.

        Instructs Xero to email the invoice to the associated contact's email address.

        Args:
            invoice: The Invoice to email. Must have a billing_service_invoice_id.
        """
        if settings.XERO_EMAIL_INVOICES:
            self._get_authentication_token()
            self._email_invoice(invoice.billing_service_invoice_id)

    def update_invoices(self, billing_service_invoice_ids: list[str]) -> None:
        """Update local invoice records with latest data from Xero.

        Fetches current invoice details from Xero and updates the corresponding
        local Invoice records with amounts, dates, and payment status. Marks
        invoices as no longer needing updates.

        Args:
            billing_service_invoice_ids: List of Xero invoice IDs to update.
        """
        self._get_authentication_token()

        invoices: list[AccountingInvoice] = self._get_xero_invoices(
            billing_service_invoice_ids,
        )
        for accounting_invoice in invoices:
            invoice = Invoice.objects.get(
                billing_service_invoice_id=accounting_invoice.invoice_id,
            )
            invoice.amount = accounting_invoice.total
            invoice.issue_date = accounting_invoice.date
            invoice.due_date = accounting_invoice.due_date
            invoice.paid = accounting_invoice.amount_paid
            invoice.due = accounting_invoice.amount_due
            invoice.paid_date = accounting_invoice.fully_paid_on_date
            invoice.update_needed = False
            invoice.save()


class MockXeroBillingService(XeroBillingService):
    """Mock Xero service for testing and development."""

    def _get_client_credentials_token(self) -> None:
        """Mock token acquisition by setting a dummy token.

        Overrides the parent method to avoid actual OAuth2 requests during testing.
        """
        self.set_xero_token("token")

    def _create_xero_contact(self, contact_params: dict[str, Any]) -> str:
        """Mock contact creation by returning a dummy contact ID.

        Args:
            contact_params: Dictionary of contact attributes (ignored).

        Returns:
            A static mock contact ID string.
        """
        return "mock-xero-contact-id"

    def _update_xero_contact(
        self,
        contact_id: str,
        contact_params: dict[str, Any],
    ) -> None:
        """Mock contact update by doing nothing.

        Args:
            contact_id: The contact ID to update (ignored).
            contact_params: Dictionary of contact attributes (ignored).
        """
        return

    def _get_xero_invoices(
        self,
        billing_service_invoice_ids: list[str],
    ) -> list[AccountingInvoice]:
        """Mock invoice retrieval by returning an empty list.

        Args:
            billing_service_invoice_ids: List of invoice IDs (ignored).

        Returns:
            An empty list.
        """
        return []

    def _get_connections(self) -> list[Connection]:
        """Mock connections retrieval by returning an empty list.

        Returns:
            An empty list of connections.
        """
        return []

    def _email_invoice(self, billing_service_invoice_id: str) -> None:
        """Mock invoice email by doing nothing.

        Args:
            billing_service_invoice_id: The invoice ID to email (ignored).
        """
        return

    def _get_online_invoice_url(self, billing_service_invoice_id: str) -> str:
        """Mock the online invoice URL from Xero.

        Args:
            billing_service_invoice_id: The Xero invoice ID.

        Returns:
            The online invoice URL from Xero.
        """
        return

    def _create_xero_invoice(
        self,
        contact_id: str,
        invoice_details: dict[str, Any],
        line_item_details: list[dict[str, Any]],
    ) -> AccountingInvoice:
        """Mock invoice creation by returning a fake AccountingInvoice.

        Calculates the total from line items and returns a mock invoice object
        with a static invoice ID and number.

        Args:
            contact_id: The contact ID (ignored).
            invoice_details: Dictionary containing 'date' and 'due_date' keys.
            line_item_details: List of dictionaries with 'unit_amount' and 'quantity'.

        Returns:
            A mock AccountingInvoice object with calculated totals.
        """
        total = 0
        for line_item in line_item_details:
            total += line_item["unit_amount"] * line_item["quantity"]

        invoice: AccountingInvoice = AccountingInvoice(
            invoice_id="e576f965-f2fb-459f-9ea8-035424ae31d7",
            invoice_number="INV-1234",
            date=str(invoice_details["date"]),
            due_date=str(invoice_details["due_date"]),
            total=total,
            amount_due=total,
            amount_paid=0,
        )
        return invoice
