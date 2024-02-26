from typing import Any

from django.utils.translation import gettext_lazy as _
from django_tables2 import Column, DateColumn, Table, TemplateColumn

from .models import Account, Invoice


class AdminInvoiceTable(Table):
    invoice_number = Column(verbose_name=_("Invoice Number"))
    to = Column(accessor="account", verbose_name=_("To"), orderable=False)
    type = Column(accessor="account", verbose_name=_("Type"), orderable=False)
    issue_date = DateColumn(verbose_name=_("Issue Date"), short=True)
    due_date = DateColumn(verbose_name=_("Due Date"), short=True)
    amount = Column(verbose_name=_("Amount"), orderable=False)
    paid = Column(verbose_name=_("Paid"), orderable=False)
    due = Column(verbose_name=_("Due"), orderable=False)

    def render_to(self, value: Account, record: Invoice) -> Any:
        if value.user_id:
            return value.user.username
        elif value.organisation_id:
            return value.organisation.name
        return None

    def render_type(self, value: Account, record: Invoice) -> Any:
        if value.user_id:
            return _("User")
        elif value.organisation_id:
            return _("Organisation")
        return None

    class Meta:
        fields = ("invoice_number", "to", "type", "issue_date", "due_date", "amount", "paid", "due")
        order_by = ("-invoice_number",)
        model = Invoice


class InvoiceTable(Table):
    invoice_number = Column(verbose_name=_("Invoice Number"))
    issue_date = DateColumn(verbose_name=_("Issue Date"), short=True)
    due_date = DateColumn(verbose_name=_("Due Date"), short=True)
    amount = Column(verbose_name=_("Amount"), orderable=False)
    paid = Column(verbose_name=_("Paid"), orderable=False)
    due = Column(verbose_name=_("Due"), orderable=False)
    actions = TemplateColumn(verbose_name=_("Actions"), template_name="invoice_actions.html", orderable=False)

    class Meta:
        fields = ("invoice_number", "issue_date", "due_date", "amount", "paid", "due")
        order_by = ("-invoice_number",)
        model = Invoice
