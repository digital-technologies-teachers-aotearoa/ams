from django_tables2 import SingleTableView

from ams.users.utils import UserIsAdminMixin

from .models import Invoice
from .tables import AdminInvoiceTable


class AdminInvoiceListView(UserIsAdminMixin, SingleTableView):
    model = Invoice
    table_class = AdminInvoiceTable
    template_name = "admin_invoices.html"
    queryset = Invoice.objects.all().select_related("account__user", "account__organisation")
