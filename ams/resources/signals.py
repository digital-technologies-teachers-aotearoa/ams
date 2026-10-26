from django.db import transaction
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.dispatch import receiver

from ams.resources.cache import invalidate_resource_home_cache
from ams.resources.models import Resource
from ams.resources.models import ResourceComponent


@receiver(post_save, sender=Resource)
@receiver(post_delete, sender=Resource)
@receiver(post_save, sender=ResourceComponent)
@receiver(post_delete, sender=ResourceComponent)
def invalidate_resource_home_after_change(sender, **kwargs):
    transaction.on_commit(invalidate_resource_home_cache)
