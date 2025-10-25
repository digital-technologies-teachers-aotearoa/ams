# Permission Caching

This document explains the caching strategies implemented for the `user_has_active_membership` function to optimize performance.

## Overview

The `user_has_active_membership` function is likely to be called frequently across many page requests. Without caching, each call would execute database queries to check membership status, which can impact performance.

## Available Caching Strategies

### 1. Django Cache Framework (Default)

**Function**: `user_has_active_membership(user)`

**How it works**:

- Caches results in Django's configured cache backend (Redis, Memcached, etc.)
- Cache key: `user_has_active_membership_{user_id}`
- Cache duration: 5 minutes (300 seconds)
- Automatic cache invalidation when memberships change

**Benefits**:

- Persistent across requests and server restarts
- Shared between multiple application instances
- Automatic invalidation ensures data consistency

**Use cases**:

- Production environments
- When you need caching across multiple requests
- When data can be slightly stale (up to 5 minutes)

### 2. Request-Level Caching

**Function**: `user_has_active_membership_request_cached(user)`

**How it works**:

- Caches results as attributes on the user object
- Cache persists only for the duration of a single request
- No external cache backend required

**Benefits**:

- Always fresh data (no stale cache issues)
- No cache invalidation complexity
- Prevents multiple DB queries within the same request

**Use cases**:

- When you need very fresh data
- Development environments
- When the same permission is checked multiple times per request

## Cache Invalidation

Cache is automatically invalidated when:

- A new membership is created
- A membership is updated (status changes)
- A membership is deleted

This is handled by Django signals in `ams.utils.cache_signals`.

## Configuration

### Django Cache Backend

Ensure your Django settings include a cache configuration:

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### Cache Timeout Adjustment

To change the cache duration, modify the timeout value in `permissions.py`:

```python
# Cache for 10 minutes instead of 5
cache.set(cache_key, has_active, 600)
```

## Performance Comparison

| Strategy | First Call | Subsequent Calls | Data Freshness | Complexity |
|----------|------------|------------------|----------------|------------|
| No Cache | DB Query | DB Query | Always Fresh | Low |
| Django Cache | DB Query | Cache Hit | Up to 5 min stale | Medium |
| Request Cache | DB Query | Memory Hit | Always Fresh | Low |

## Usage Examples

```python
from ams.utils.permissions import user_has_active_membership, user_has_active_membership_request_cached

# Standard cached version (recommended for production)
if user_has_active_membership(request.user):
    # User has access
    pass

# Request-only cached version (good for development)
if user_has_active_membership_request_cached(request.user):
    # User has access
    pass
```

## Monitoring

To monitor cache performance, you can check:

- Cache hit/miss ratios in your cache backend
- Database query counts in Django Debug Toolbar
- Response times for permission-heavy pages

## Best Practices

1. **Use the default cached version** in production environments
2. **Monitor cache hit ratios** to ensure caching is effective
3. **Consider request-level caching** for development or when data must be very fresh
4. **Test cache invalidation** to ensure consistency when memberships change
5. **Be aware of cache warming** - first requests after cache expiry will be slower
