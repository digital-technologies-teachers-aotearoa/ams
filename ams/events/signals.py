from django.db import transaction
from django.db.models.signals import m2m_changed
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.dispatch import receiver

from ams.events.cache import invalidate_event_map_cache
from ams.events.models import Event
from ams.events.models import Location


@receiver(post_save, sender=Event)
@receiver(post_delete, sender=Event)
@receiver(post_save, sender=Location)
@receiver(post_delete, sender=Location)
def invalidate_event_map_after_model_change(sender, **kwargs):
    transaction.on_commit(invalidate_event_map_cache)


@receiver(m2m_changed, sender=Event.locations.through)
def invalidate_event_map_after_location_change(sender, action, **kwargs):
    if action in {"post_add", "post_remove", "post_clear"}:
        transaction.on_commit(invalidate_event_map_cache)
