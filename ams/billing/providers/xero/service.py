import json
from contextlib import suppress
from typing import TYPE_CHECKING
from typing import Any

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
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

from ams.billing.exceptions import SettingNotConfiguredError
from ams.billing.models import Account
from ams.billing.models import Invoice
from ams.billing.providers.xero.models import XeroContact
from ams.billing.services import BillingService
from ams.memberships.models import Organisation

if TYPE_CHECKING:  # pragma: no cover
    from datetime import date


class XeroBillingService(BillingService):
    """Xero accounting system integration for billing services."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.xero_token: str | None = None

        self.api_client = ApiClient(
            Configuration(
                debug=settings.DEBUG,
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
        return self.xero_token

    def set_xero_token(self, token: str) -> None:
        self.xero_token = token

    def _debug_response(self, data: Any) -> HttpResponse:
        return HttpResponse(
            json.dumps(serialize(data)),
            content_type="application/json",
        )

    def _acquire_lock(self) -> None:
        # Get an exclusive lock so only one instance can interact with Xero at a time
        # to avoid running into API limits:
        # https://developer.xero.com/documentation/guides/oauth2/limits/#api-rate-limits
        cursor = connection.cursor()
        cursor.execute("LOCK billing_xeromutex")

    def _get_client_credentials_token(self) -> None:
        self.api_client.get_client_credentials_token()

    def _get_authentication_token(self) -> None:
        if not self.get_xero_token():
            self._acquire_lock()
            self._get_client_credentials_token()

    def _get_connections(self) -> list[Connection]:
        api_instance = IdentityApi(self.api_client)
        connections: list[Connection] = api_instance.get_connections()
        return connections

    def _create_xero_contact(self, contact_params: dict[str, Any]) -> str:
        api_instance = AccountingApi(self.api_client)

        contact = Contact(**contact_params)
        contacts = Contacts(contacts=[contact])

        api_response = api_instance.create_contacts(settings.XERO_TENANT_ID, contacts)

        contact_id: str = api_response.contacts[0].contact_id
        return contact_id

    def _update_xero_contact(
        self,
        contact_id: str,
        contact_params: dict[str, Any],
    ) -> None:
        api_instance = AccountingApi(self.api_client)

        contact = Contact(**contact_params)
        contacts = Contacts(contacts=[contact])

        api_instance.update_contact(settings.XERO_TENANT_ID, contact_id, contacts)

    def _create_xero_invoice(
        self,
        contact_id: str,
        invoice_details: dict[str, Any],
        line_item_details: list[dict[str, Any]],
    ) -> AccountingInvoice:
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

    def _email_invoice(self, billing_service_invoice_id: str) -> None:
        api_instance = AccountingApi(self.api_client)
        api_instance.email_invoice(
            settings.XERO_TENANT_ID,
            billing_service_invoice_id,
            RequestEmpty(),
        )

    def _get_xero_invoices(
        self,
        billing_service_invoice_ids: list[str],
    ) -> list[AccountingInvoice]:
        api_instance = AccountingApi(self.api_client)
        api_response = api_instance.get_invoices(
            settings.XERO_TENANT_ID,
            i_ds=billing_service_invoice_ids,
        )
        invoices: list[AccountingInvoice] = api_response.invoices
        return invoices

    # NOTE: Xero contact names must be unique; we append Account.id to the name.
    # Changing Account.id sequence impacts external systems; consider carefully.
    def _xero_contact_name(self, account_id: int, name: str) -> str:
        return f"{name} ({account_id})"

    def update_user_billing_details(self, user: User) -> None:
        contact_details = {
            "name": self._xero_contact_name(user.account.pk, user.get_full_name()),
            "account_number": str(user.account.id),
            "email_address": user.email,
        }
        return self.update_account_billing_details(user.account, contact_details)

    def update_organisation_billing_details(self, organisation: Organisation) -> None:
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
        contact_id = account.xero_contact.contact_id

        if not settings.XERO_ACCOUNT_CODE:
            setting_name = "XERO_ACCOUNT_CODE"
            raise SettingNotConfiguredError(setting_name)

        if not settings.XERO_AMOUNT_TYPE:
            setting_name = "XERO_AMOUNT_TYPE"
            raise SettingNotConfiguredError(setting_name)

        if not settings.XERO_CURRENCY_CODE:
            setting_name = "XERO_CURRENCY_CODE"
            raise SettingNotConfiguredError(setting_name)

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
        self._get_authentication_token()
        self._email_invoice(invoice.billing_service_invoice_id)

    def update_invoices(self, billing_service_invoice_ids: list[str]) -> None:
        """Update invoices with latest data from Xero."""
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
        self.set_xero_token("token")

    def _create_xero_contact(self, contact_params: dict[str, Any]) -> str:
        return "mock-xero-contact-id"

    def _update_xero_contact(
        self,
        contact_id: str,
        contact_params: dict[str, Any],
    ) -> None:
        return

    def _get_xero_invoices(
        self,
        billing_service_invoice_ids: list[str],
    ) -> list[AccountingInvoice]:
        return []

    def _get_connections(self) -> list[Connection]:
        return []

    def _email_invoice(self, billing_service_invoice_id: str) -> None:
        return

    def _create_xero_invoice(
        self,
        contact_id: str,
        invoice_details: dict[str, Any],
        line_item_details: list[dict[str, Any]],
    ) -> AccountingInvoice:
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
