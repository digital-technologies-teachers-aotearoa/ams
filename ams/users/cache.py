from django.core.cache import cache

from ams.users.models import ProfileField

PROFILE_COMPLETION_FIELD_COUNT_CACHE_KEY = "ams:profile-completion-field-count:v1"
PROFILE_COMPLETION_FIELD_COUNT_CACHE_TTL = 300


def profile_completion_field_count() -> int:
    cached_count = cache.get(PROFILE_COMPLETION_FIELD_COUNT_CACHE_KEY)
    if cached_count is not None:
        return cached_count

    count = ProfileField.objects.filter(
        is_active=True,
        counts_toward_completion=True,
    ).count()
    cache.set(
        PROFILE_COMPLETION_FIELD_COUNT_CACHE_KEY,
        count,
        PROFILE_COMPLETION_FIELD_COUNT_CACHE_TTL,
    )
    return count


def invalidate_profile_completion_field_count() -> None:
    cache.delete(PROFILE_COMPLETION_FIELD_COUNT_CACHE_KEY)
