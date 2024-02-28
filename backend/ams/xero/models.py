from django.db.models import CASCADE, CharField, Model, OneToOneField

from ams.billing.models import Account


class XeroContact(Model):
    account = OneToOneField(Account, on_delete=CASCADE, related_name="xero_contact")
    contact_id = CharField(max_length=255, unique=True)


class XeroMutex(Model):
    pass
