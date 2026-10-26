from django.core.cache import cache

RESOURCE_HOME_CACHE_TTL = 60
RESOURCE_HOME_CACHE_KEY_PREFIX = "ams:resources-home:v1"


def resource_home_cache_key(*, is_member: bool) -> str:
    visibility = "member" if is_member else "nonmember"
    return f"{RESOURCE_HOME_CACHE_KEY_PREFIX}:{visibility}"


def invalidate_resource_home_cache() -> None:
    cache.delete(resource_home_cache_key(is_member=True))
    cache.delete(resource_home_cache_key(is_member=False))
