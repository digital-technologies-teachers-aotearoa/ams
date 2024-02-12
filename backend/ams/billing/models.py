from django.contrib.auth.models import User
from django.db.models import (
    CASCADE,
    CharField,
    CheckConstraint,
    DateField,
    DecimalField,
    ForeignKey,
    Model,
    OneToOneField,
    Q,
)

from ams.users.models import Organisation


class Account(Model):
    organisation = OneToOneField(Organisation, null=True, on_delete=CASCADE, related_name="account")
    user = OneToOneField(User, null=True, on_delete=CASCADE, related_name="account")

    class Meta:
        constraints = [
            CheckConstraint(
                check=Q(organisation__isnull=False) | Q(user__isnull=False),
                name="check_has_user_or_organisation",
            ),
        ]


class Invoice(Model):
    account = ForeignKey(Account, on_delete=CASCADE, related_name="invoices")
    invoice_number = CharField(max_length=255, unique=True)
    issue_date = DateField()
    due_date = DateField()
    amount = DecimalField(max_digits=10, decimal_places=2)
    paid = DecimalField(max_digits=10, decimal_places=2)
    due = DecimalField(max_digits=10, decimal_places=2)
