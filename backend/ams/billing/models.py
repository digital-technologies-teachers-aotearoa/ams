from typing import Any

from django.contrib.auth.models import User
from django.db.models import (
    CASCADE,
    BooleanField,
    CharField,
    CheckConstraint,
    DateField,
    DecimalField,
    ForeignKey,
    Model,
    OneToOneField,
    Q,
)
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from ams.users.models import MembershipStatus, Organisation


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
    paid_date = DateField(null=True)
    amount = DecimalField(max_digits=10, decimal_places=2)
    paid = DecimalField(max_digits=10, decimal_places=2)
    due = DecimalField(max_digits=10, decimal_places=2)
    billing_service_invoice_id = CharField(max_length=255, unique=True, null=True)
    update_needed = BooleanField(default=False)


@receiver(pre_save, sender=Invoice)
def approve_paid_user_membership(sender: Any, instance: Invoice, **kwargs: Any) -> None:
    # When the invoice for an active user's membership is paid, approve the membership
    if instance.pk and instance.paid_date:
        if Invoice.objects.get(pk=instance.pk).paid_date is None:
            user_membership = instance.user_memberships.all().first()
            if (
                user_membership
                and user_membership.status() == MembershipStatus.PENDING
                and user_membership.user.is_active
            ):
                user_membership.approved_datetime = timezone.now()
                user_membership.save()
