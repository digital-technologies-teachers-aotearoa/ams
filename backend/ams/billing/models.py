from django.contrib.auth.models import User
from django.db.models import CASCADE, CheckConstraint, Model, OneToOneField, Q

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
