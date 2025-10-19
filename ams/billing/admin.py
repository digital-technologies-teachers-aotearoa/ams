from django.contrib import admin

from .models import Account
from .models import Invoice


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("organisation", "user")
    search_fields = ("organisation__name", "user__email")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "account",
        "invoice_number",
        "issue_date",
        "due_date",
        "paid_date",
        "amount",
        "paid",
        "due",
        "update_needed",
    )
    search_fields = (
        "invoice_number",
        "account__organisation__name",
        "account__user__email",
    )
    list_filter = ("issue_date", "due_date", "paid_date", "update_needed")
