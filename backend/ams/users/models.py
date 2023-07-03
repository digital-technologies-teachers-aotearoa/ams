from django.contrib.auth.models import User
from django.db.models import (
    CASCADE,
    CharField,
    DateTimeField,
    DecimalField,
    ForeignKey,
    Model,
    TextChoices,
)
from django.utils.translation import gettext_lazy as _
from relativedeltafield import RelativeDeltaField


class MembershipOptionType(TextChoices):
    INDIVIDUAL = "INDIVIDUAL", _("Individual")
    ORGANISATION = "ORGANISATION", _("Organisation")


class MembershipOption(Model):
    name = CharField(max_length=255, unique=True)
    type = CharField(max_length=255, choices=MembershipOptionType.choices)
    duration = RelativeDeltaField()
    cost = DecimalField(max_digits=10, decimal_places=2)


class UserMembership(Model):
    user = ForeignKey(User, on_delete=CASCADE, related_name="user_memberships")
    membership_option = ForeignKey(MembershipOption, on_delete=CASCADE, related_name="user_memberships")
    created_datetime = DateTimeField()
    approved_datetime = DateTimeField(null=True)
