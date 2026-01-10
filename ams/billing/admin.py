from django.contrib import admin

from .models import Account
from .models import Invoice


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("organisation", "user")
    search_fields = ("organisation__name", "user__email")
    readonly_fields = ("organisation", "user")


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
    readonly_fields = (
        "account",
        "invoice_number",
        "issue_date",
        "due_date",
        "paid_date",
        "amount",
        "paid",
        "due",
        "billing_service_invoice_id",
        "individual_membership",
        "organisation_membership",
    )
    fieldsets = (
        (
            "Billing Integration",
            {
                "fields": (
                    "update_needed",
                    "billing_service_invoice_id",
                ),
                "description": "Enabling 'Update needed' will force the invoice "
                "to update in the next update cycle.",
            },
        ),
        (
            "Invoice",
            {
                "fields": (
                    "invoice_number",
                    "issue_date",
                    "due_date",
                    "paid_date",
                    "amount",
                    "paid",
                    "due",
                ),
            },
        ),
        (
            "Related models",
            {
                "fields": (
                    "account",
                    "individual_membership",
                    "organisation_membership",
                ),
            },
        ),
    )
