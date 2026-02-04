from django.contrib.auth import get_user_model
from django.db.models import CASCADE
from django.db.models import BooleanField
from django.db.models import CharField
from django.db.models import CheckConstraint
from django.db.models import DateField
from django.db.models import DecimalField
from django.db.models import ForeignKey
from django.db.models import Index
from django.db.models import Model
from django.db.models import OneToOneField
from django.db.models import Q

from ams.organisations.models import Organisation

User = get_user_model()


class Account(Model):
    organisation = OneToOneField(
        Organisation,
        null=True,
        blank=True,
        on_delete=CASCADE,
        related_name="account",
    )
    user = OneToOneField(
        User,
        null=True,
        blank=True,
        on_delete=CASCADE,
        related_name="account",
    )

    class Meta:
        constraints = [
            CheckConstraint(
                condition=Q(organisation__isnull=False) | Q(user__isnull=False),
                name="check_has_user_or_organisation",
            ),
        ]

    def __str__(self):
        if self.organisation:
            return f"Account for {self.organisation.name}"
        if self.user:
            return f"Account for {self.user.get_full_name()}"
        return "Unassigned Account"


class Invoice(Model):
    account = ForeignKey(Account, on_delete=CASCADE, related_name="invoices")
    invoice_number = CharField(max_length=255, unique=True)
    issue_date = DateField()
    due_date = DateField()
    paid_date = DateField(null=True, blank=True)
    amount = DecimalField(max_digits=10, decimal_places=2)
    paid = DecimalField(max_digits=10, decimal_places=2)
    due = DecimalField(max_digits=10, decimal_places=2)
    billing_service_invoice_id = CharField(max_length=255, unique=True)
    update_needed = BooleanField(default=False)
    individual_membership = ForeignKey(
        "memberships.IndividualMembership",
        on_delete=CASCADE,
        null=True,
        blank=True,
        related_name="invoices",
    )
    organisation_membership = ForeignKey(
        "memberships.OrganisationMembership",
        on_delete=CASCADE,
        null=True,
        blank=True,
        related_name="invoices",
    )

    class Meta:
        indexes = [
            Index(
                fields=["individual_membership", "paid_date"],
                name="idx_invoice_indiv",
            ),
            Index(
                fields=["organisation_membership", "paid_date"],
                name="idx_invoice_org",
            ),
        ]

    def __str__(self):
        return f"Invoice {self.invoice_number} for {self.account}"
