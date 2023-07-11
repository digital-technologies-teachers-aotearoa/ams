from django.db.models import CharField, DecimalField, Model, TextChoices
from django.utils.translation import gettext_lazy as _
from relativedeltafield import RelativeDeltaField


class MembershipOption(Model):
    class MembershipOptionType(TextChoices):
        INDIVIDUAL = "INDIVIDUAL", _("Individual")
        ORGANISATION = "ORGANISATION", _("Organisation")

    name = CharField(max_length=255, unique=True)
    type = CharField(max_length=255, choices=MembershipOptionType.choices)
    duration = RelativeDeltaField()
    cost = DecimalField(max_digits=10, decimal_places=2)
