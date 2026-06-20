from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Account
from .models import Invoice


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("organisation", "user")
    search_fields = ("organisation__name", "user__email")
    readonly_fields = ("organisation", "user")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    actions = ["mark_update_needed"]
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
            _("Billing Integration"),
            {
                "fields": (
                    "update_needed",
                    "billing_service_invoice_id",
                ),
                "description": _(
                    "Enabling 'Update needed' will force the invoice "
                    "to update in the next update cycle.",
                ),
            },
        ),
        (
            _("Invoice"),
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
            _("Related models"),
            {
                "fields": (
                    "account",
                    "individual_membership",
                    "organisation_membership",
                ),
            },
        ),
    )

    @admin.action(description=_("Mark selected invoices for update"))
    def mark_update_needed(self, request, queryset):
        queryset.update(update_needed=True)
