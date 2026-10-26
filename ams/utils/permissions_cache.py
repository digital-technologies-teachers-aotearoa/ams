from django.core.cache import cache

USER_ACTIVE_MEMBERSHIP_CACHE_KEY_PREFIX = "ams:user-active-membership:v1"
USER_ACTIVE_MEMBERSHIP_CACHE_TTL = 3600


def user_active_membership_cache_key(user_id: int) -> str:
    return f"{USER_ACTIVE_MEMBERSHIP_CACHE_KEY_PREFIX}:{user_id}"


def get_cached_user_active_membership(user_id: int) -> bool | None:
    return cache.get(user_active_membership_cache_key(user_id))


def set_cached_user_active_membership(
    user_id: int,
    *,
    has_membership: bool,
) -> None:
    cache.set(
        user_active_membership_cache_key(user_id),
        has_membership,
        USER_ACTIVE_MEMBERSHIP_CACHE_TTL,
    )


def invalidate_user_active_membership_cache(user_id: int) -> None:
    cache.delete(user_active_membership_cache_key(user_id))
