from django.conf import settings
from django.core.cache import cache

EVENT_MAP_CACHE_TTL = 300
EVENT_MAP_CACHE_KEY_PREFIX = "ams:events-home-map:v1"


def event_map_cache_key(language_code: str | None) -> str:
    return f"{EVENT_MAP_CACHE_KEY_PREFIX}:{language_code or settings.LANGUAGE_CODE}"


def invalidate_event_map_cache() -> None:
    for language_code, _name in settings.LANGUAGES:
        cache.delete(event_map_cache_key(language_code))
