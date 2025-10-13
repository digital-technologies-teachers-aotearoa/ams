from django.db.models import CASCADE
from django.db.models import CharField
from django.db.models import Model
from django.db.models import OneToOneField

from ams.billing.models import Account


class XeroContact(Model):
    account = OneToOneField(Account, on_delete=CASCADE, related_name="xero_contact")
    contact_id = CharField(max_length=255, unique=True)

    def __str__(self):
        return f"XeroContact(account={self.account}, contact_id={self.contact_id})"


class XeroMutex(Model):
    def __str__(self):
        return "Xero Mutex (Exclusive Lock)"
