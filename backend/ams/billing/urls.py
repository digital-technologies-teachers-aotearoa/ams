from django.urls import path

from .views import AdminInvoiceListView

urlpatterns = [
    path("invoices/", AdminInvoiceListView.as_view(), name="admin-invoice-list"),
]
