import json
from datetime import date
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import HttpResponse
from xero_python.accounting import AccountingApi, Contact, Contacts, CurrencyCode
from xero_python.accounting import Invoice as AccountingInvoice
from xero_python.accounting import Invoices, LineAmountTypes, LineItem
from xero_python.api_client import ApiClient
from xero_python.api_client.configuration import Configuration
from xero_python.api_client.oauth2 import OAuth2Token
from xero_python.api_client.serializer import serialize

from ams.billing.models import Account, Invoice
from ams.billing.service import BillingService
from ams.users.models import Organisation

from .models import XeroContact


class XeroBillingService(BillingService):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.xero_token: Optional[str] = None

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

    def get_xero_token(self) -> Optional[str]:
        return self.xero_token

    def set_xero_token(self, token: str) -> None:
        self.xero_token = token

    def _debug_response(self, data: Any) -> HttpResponse:
        return HttpResponse(json.dumps(serialize(data)), content_type="application/json")

    def _get_authentication_token(self) -> None:
        self.api_client.get_client_credentials_token()

    def _create_xero_contact(self, contact_params: Dict[str, Any]) -> str:
        api_instance = AccountingApi(self.api_client)

        contact = Contact(**contact_params)
        contacts = Contacts(contacts=[contact])

        api_response = api_instance.create_contacts(settings.XERO_TENANT_ID, contacts)

        contact_id: str = api_response.contacts[0].contact_id
        return contact_id

    def _update_xero_contact(self, contact_id: str, contact_params: Dict[str, Any]) -> None:
        api_instance = AccountingApi(self.api_client)

        contact = Contact(**contact_params)
        contacts = Contacts(contacts=[contact])

        api_instance.update_contact(settings.XERO_TENANT_ID, contact_id, contacts)

    def _create_xero_invoice(
        self, contact_id: str, invoice_details: Dict[str, Any], line_item_details: List[Dict[str, Any]]
    ) -> AccountingInvoice:
        api_instance = AccountingApi(self.api_client)

        contact = Contact(contact_id=contact_id)

        line_items = [LineItem(**item_details) for item_details in line_item_details]

        invoice = AccountingInvoice(contact=contact, line_items=line_items, **invoice_details)
        invoices = Invoices(invoices=[invoice])

        api_response = api_instance.create_invoices(settings.XERO_TENANT_ID, invoices)

        response_invoice: AccountingInvoice = api_response.invoices[0]
        return response_invoice

    def _get_xero_invoices(self, billing_service_invoice_ids: List[str]) -> List[AccountingInvoice]:
        api_instance = AccountingApi(self.api_client)
        api_response = api_instance.get_invoices(settings.XERO_TENANT_ID, i_ds=billing_service_invoice_ids)
        invoices: List[AccountingInvoice] = api_response.invoices
        return invoices

    # NOTE: The name in xero needs to be unique so we combined a name with Account.id primary key
    # For this reason it is important to not to change the Account.id sequence without considering
    # the implications to external systems
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

        return self.update_account_billing_details(organisation.account, contact_details)

    def update_account_billing_details(self, account: Account, contact_details: Dict[str, Any]) -> None:
        contact_id: Optional[str] = None

        try:
            contact_id = account.xero_contact.contact_id
        except ObjectDoesNotExist:
            pass

        self._get_authentication_token()

        if contact_id:
            self._update_xero_contact(contact_id, contact_details)
        else:
            contact_id = self._create_xero_contact(contact_details)

            XeroContact.objects.create(account=account, contact_id=contact_id)

    def create_invoice(self, account: Account, date: date, due_date: date, line_items: List[Dict[str, Any]]) -> None:
        contact_id = account.xero_contact.contact_id

        if not settings.XERO_ACCOUNT_CODE:
            raise Exception("XERO_ACCOUNT_CODE setting not configured")

        if not settings.XERO_AMOUNT_TYPE:
            raise Exception("XERO_AMOUNT_TYPE setting not configured")

        if not settings.XERO_CURRENCY_CODE:
            raise Exception("XERO_CURRENCY_CODE setting not configured")

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

        invoice = self._create_xero_invoice(contact_id, invoice_details, line_items)

        Invoice.objects.create(
            account=account,
            billing_service_invoice_id=invoice.invoice_id,
            invoice_number=invoice.invoice_number,
            issue_date=invoice.date,
            due_date=invoice.due_date,
            amount=invoice.total,
            due=invoice.amount_due,
            paid=invoice.amount_paid,
        )

    def update_invoices(self, billing_service_invoice_ids: List[str]) -> None:
        self._get_authentication_token()

        invoices: List[AccountingInvoice] = self._get_xero_invoices(billing_service_invoice_ids)
        for accounting_invoice in invoices:
            invoice = Invoice.objects.get(billing_service_invoice_id=accounting_invoice.invoice_id)
            invoice.amount = accounting_invoice.total
            invoice.issue_date = accounting_invoice.date
            invoice.due_date = accounting_invoice.due_date
            invoice.paid = accounting_invoice.amount_paid
            invoice.due = accounting_invoice.amount_due
            invoice.save()


class MockXeroBillingService(XeroBillingService):
    def _get_authentication_token(self) -> None:
        return

    def _create_xero_contact(self, contact_params: Dict[str, Any]) -> str:
        return "mock-xero-contact-id"

    def _update_xero_contact(self, contact_id: str, contact_params: Dict[str, Any]) -> None:
        return

    def _get_xero_invoices(self, invoice_ids: List[str]) -> List[AccountingInvoice]:
        return []

    def _create_xero_invoice(
        self, contact_id: str, invoice_details: Dict[str, Any], line_item_details: List[Dict[str, Any]]
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
