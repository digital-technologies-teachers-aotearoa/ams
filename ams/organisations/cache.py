from django.core.cache import cache

ORGANISATION_ADMIN_CACHE_KEY_PREFIX = "ams:organisation-admin:v1"
ORGANISATION_ADMIN_CACHE_TTL = 300


def organisation_admin_cache_key(user_id: int, organisation_id: int) -> str:
    return f"{ORGANISATION_ADMIN_CACHE_KEY_PREFIX}:{user_id}:{organisation_id}"


def get_cached_organisation_admin(user_id: int, organisation_id: int) -> bool | None:
    return cache.get(organisation_admin_cache_key(user_id, organisation_id))


def set_cached_organisation_admin(
    user_id: int,
    organisation_id: int,
    *,
    is_admin: bool,
) -> None:
    cache.set(
        organisation_admin_cache_key(user_id, organisation_id),
        is_admin,
        ORGANISATION_ADMIN_CACHE_TTL,
    )


def invalidate_organisation_admin_cache(user_id: int, organisation_id: int) -> None:
    cache.delete(organisation_admin_cache_key(user_id, organisation_id))
