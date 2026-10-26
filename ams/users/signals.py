from django.db import transaction
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.dispatch import receiver

from ams.users.cache import invalidate_profile_completion_field_count
from ams.users.models import ProfileField


@receiver(post_save, sender=ProfileField)
@receiver(post_delete, sender=ProfileField)
def invalidate_profile_completion_count_after_change(sender, **kwargs):
    transaction.on_commit(invalidate_profile_completion_field_count)
