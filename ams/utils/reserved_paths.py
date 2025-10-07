"""
Centralized reserved paths for AMS project.
These paths are used for Django apps and must not be treated as locale codes or CMS
slugs.

The reserved paths are dynamically extracted from the URL configuration to ensure
they stay in sync with the actual routes defined in config/urls.py.

Key benefits of dynamic extraction:
- Single source of truth: URL patterns defined in config/urls.py
- No manual synchronization needed across multiple files
- Automatically picks up new reserved paths when URLs are added
- Works with both top-level patterns and i18n_patterns
- Includes fallback for early initialization phases

Usage:
    from ams.utils.reserved_paths import get_reserved_paths_set

    reserved = get_reserved_paths_set()
    if slug in reserved:
        raise ValidationError("This slug is reserved")
"""

from django.conf import settings
from django.urls import get_resolver


def get_reserved_paths():  # noqa: C901
    """
    Extract reserved path prefixes from the URL configuration.

    Returns a list of path prefixes that are reserved for Django applications
    and should not be used as locale codes or CMS page slugs.
    """
    reserved = set()

    try:
        # Get the root URL resolver
        resolver = get_resolver()

        def extract_paths(patterns):
            """Recursively extract path prefixes from URL patterns."""
            for pattern in patterns:
                if hasattr(pattern, "pattern") and hasattr(pattern.pattern, "_route"):
                    route = pattern.pattern._route  # noqa: SLF001
                    # Extract the first segment (e.g., "billing/" -> "billing")
                    if route and route != "":
                        first_segment = route.split("/")[0]
                        if first_segment:
                            reserved.add(first_segment)

                # Also check nested patterns (e.g., from i18n_patterns)
                if hasattr(pattern, "url_patterns"):
                    extract_paths(pattern.url_patterns)

        # Extract from root URL patterns
        extract_paths(resolver.url_patterns)

        # Also include the admin URL from settings (may be dynamic)
        if hasattr(settings, "ADMIN_URL"):
            admin_url = settings.ADMIN_URL
            if admin_url:
                # Extract first segment from admin URL (e.g., "admin/" -> "admin")
                admin_segment = admin_url.strip("/").split("/")[0]
                if admin_segment:
                    reserved.add(admin_segment)

    except Exception:  # noqa: BLE001
        # Fallback to hardcoded list if dynamic extraction fails
        # (e.g., during early Django initialization)
        reserved = {
            "admin",
            "billing",
            "users",
            "forum",
            "cms",
            "cms-documents",
            "accounts",
        }

    return sorted(reserved)


def get_reserved_paths_list():
    """Get reserved paths as a list."""
    return get_reserved_paths()


def get_reserved_paths_set():
    """Get reserved paths as a set."""
    return set(get_reserved_paths())
