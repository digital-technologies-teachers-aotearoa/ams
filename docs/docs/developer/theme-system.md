# Theming

This document provides technical details about the AMS theme customization system for developers.

## Architecture Overview

The theme system allows runtime customization of Bootstrap 5.3 CSS variables through Django/Wagtail admin without code deployments. It consists of:

1. **Database Model**: `ThemeSettings` (Wagtail site setting)
2. **Template Tag**: Renders theme CSS on demand
3. **Caching Layer**: Two-tier cache for optimal performance
4. **Template System**: Renders CSS custom properties
5. **Signal Handlers**: Manage cache invalidation

!!! note "Dark Mode Not Currently Supported"
    The ThemeSettings model includes fields for dark mode colors (commented out), but dark mode switching is not yet implemented. Only light mode colors are currently active in the admin interface.

## Database Schema

### ThemeSettings Model

Located in `ams/cms/models/theme.py`:

```python
@register_setting
class ThemeSettings(BaseSiteSetting):
    """Theme customization settings for Bootstrap CSS variables."""

    cache_version = models.IntegerField(default=1, editable=False)

    # 40+ ColorField attributes for various Bootstrap variables
    # Examples:
    primary_color = ColorField(default="#0d6efd")
    body_bg_light = ColorField(default="#ffffff")
    # Dark mode fields are commented out (not currently supported)
    # body_bg_dark = ColorField(default="#212529")
    # ... etc

    # Typography
    font_sans_serif = models.CharField(max_length=500)
    body_font_size = models.CharField(max_length=50)

    # Advanced
    custom_css = models.TextField(blank=True)
```

**Key Features:**

- Inherits from `BaseSiteSetting` for per-site configuration
- `cache_version` field auto-increments on save for cache invalidation
- All color fields validated as hex codes via `ColorField`
- Automatically creates revision snapshots on each save

### ThemeSettingsRevision Model

Stores complete version history:

```python
class ThemeSettingsRevision(models.Model):
    """Historical snapshot of ThemeSettings."""
    settings = models.ForeignKey(ThemeSettings)
    data = models.JSONField()  # Complete settings snapshot
    created_at = models.DateTimeField(auto_now_add=True)
```

Enables audit trail and potential rollback functionality.

## Caching Strategy

### Two-Tier Cache Architecture

The system uses an optimized two-tier caching approach to minimize database queries:

```text
┌─────────────────────────────────────────┐
│ Request → Template Tag                  │
└──────────────┬──────────────────────────┘
               ▼
    ┌───────────────────────┐
    │ Tier 1: Version Check │ ← Lightweight (integer only)
    │ Key: theme_version_   │   ~8 bytes in cache
    │      site{site_id}    │
    └──────────┬────────────┘
               │
         ┌─────▼─────┐
         │  Cached?  │
         └─────┬─────┘
           Yes │ No
               │  │
               ▼  ▼
    ┌──────────────────────┐  ┌──────────────┐
    │ Tier 2: CSS Cache    │  │ Query DB     │
    │ Key: theme_css_v{N}_ │  │ Render CSS   │
    │      site{site_id}   │  │ Cache both   │
    └──────────┬───────────┘  └──────┬───────┘
               │                     │
               └─────────┬───────────┘
                         ▼
                  Return CSS to template
```

### Cache Keys

Two types of cache keys are used:

1. **Version Cache**: `theme_version_site{site_id}`
   - Stores: Integer (cache_version field value)
   - Size: ~8 bytes
   - Purpose: Quick version check without full object retrieval

2. **CSS Cache**: `theme_css_v{version}_site{site_id}`
   - Stores: Rendered HTML string with `<style>` tags
   - Size: ~2-5 KB
   - Purpose: Complete rendered CSS for immediate use

### Cache Flow

**First Request (Cache Miss):**

1. Context processor checks version cache → Miss
2. Queries database for `ThemeSettings` object
3. Renders CSS template with settings
4. Stores both version and CSS in cache (TTL: infinite)
5. Returns rendered CSS

**Subsequent Requests (Cache Hit):**

1. Context processor checks version cache → Hit (gets version number)
2. Checks CSS cache for that version → Hit
3. Returns cached CSS (no DB query, no rendering)

**After Theme Update:**

1. Admin saves settings → `cache_version` increments
2. Signal handler updates version cache to new version
3. Old CSS cache becomes stale (different version)
4. Next request detects version change, re-renders and caches

### Performance Characteristics

| Metric | Value |
|--------|-------|
| Cache lookups per request | 1-2 (version check, then CSS if hit) |
| Database queries (cached) | 0 |
| Database queries (cache miss) | 1 |
| Rendering time (cached) | 0ms |
| Rendering time (cache miss) | ~5-10ms |
| Cache invalidation delay | Immediate |
| Memory per site | ~5-10 KB |

## Template Tag

Located in `ams/cms/templatetags/cms_tags.py`:

```python
@register.simple_tag(takes_context=True)
def theme_css(context):
    """Render theme CSS with optimized caching."""
    request = context.get("request")
    if not request:
        return ""

    site = Site.find_for_request(request)
    if not site:
        return ""

    # Two-tier cache keys
    version_cache_key = f"theme_version_site{site.id}"
    css_cache_key_template = "theme_css_v{version}_site{site_id}"

    # Step 1: Check version cache
    cached_version = cache.get(version_cache_key)

    if cached_version is not None:
        # Step 2: Try CSS cache for this version
        css_cache_key = css_cache_key_template.format(
            version=cached_version,
            site_id=site.id
        )
        cached_css = cache.get(css_cache_key)

        if cached_css is not None:
            return cached_css

    # Step 3: Cache miss - query and render
    theme_settings_obj = ThemeSettings.for_site(site)
    html = render_to_string("templatetags/theme_css.html",
                           {"theme": theme_settings_obj})

    # Step 4: Update both cache tiers
    cache.set(version_cache_key, theme_settings_obj.cache_version, None)
    cache.set(css_cache_key, html, None)

    return html
```

**Usage** - The template tag must be loaded in templates where it's used:

```django
{% load cms_tags %}
{% theme_css %}
```

## Signal Handlers

Located in `ams/cms/signals.py`:

### Post-Save Signal

```python
@receiver(post_save, sender=ThemeSettings)
def clear_theme_cache_on_save(sender, instance, **kwargs):
    """Clear old cache and update version cache on save."""
    # Clear previous version's CSS cache
    if instance.cache_version > 1:
        old_css_key = f"theme_css_v{instance.cache_version - 1}_site{instance.site_id}"
        cache.delete(old_css_key)

    # Update version cache to trigger invalidation
    version_key = f"theme_version_site{instance.site_id}"
    cache.set(version_key, instance.cache_version, None)
```

### Post-Delete Signal

```python
@receiver(post_delete, sender=ThemeSettings)
def clear_theme_cache_on_delete(sender, instance, **kwargs):
    """Clear both cache tiers when settings deleted."""
    css_key = f"theme_css_v{instance.cache_version}_site{instance.site_id}"
    version_key = f"theme_version_site{instance.site_id}"
    cache.delete(css_key)
    cache.delete(version_key)
```

## Template Integration

### Base Template

In `ams/templates/includes/head.html`:

```django
{% load static i18n wagtailimages_tags cms_tags %}

<head>
  <!-- ... -->
  <link href="{% static 'css/project.min.css' %}" rel="stylesheet" />
  {% theme_css %}
</head>
```

The `theme_css` template tag is called explicitly where needed. It automatically retrieves the request from the template context.

### Generated CSS Structure

The `templatetags/theme_css.html` template generates:

```html
<style>
:root,
[data-bs-theme="light"] {
  /* Body colors */
  --bs-body-color: {{ theme.body_color_light }};
  --bs-body-bg: {{ theme.body_bg_light }};
  --bs-body-color-rgb: {{ theme.body_color_light|hex_to_rgb }};
  --bs-body-bg-rgb: {{ theme.body_bg_light|hex_to_rgb }};

  /* Theme colors */
  --bs-primary: {{ theme.primary_color }};
  --bs-primary-rgb: {{ theme.primary_color|hex_to_rgb }};

  /* ... 100+ CSS variables ... */
}

<!-- Dark mode section currently disabled -->
<!-- [data-bs-theme="dark"] {
  --bs-body-color: {{ theme.body_color_dark }};
  --bs-body-bg: {{ theme.body_bg_dark }};
} -->

/* Custom CSS (if provided) */
{{ theme.custom_css }}
</style>
```

## Template Tags

Located in `config/templatetags/theme.py`:

### hex_to_rgb Filter

Converts hex colors to RGB format for CSS rgb() values:

```python
@register.filter
def hex_to_rgb(hex_color):
    """Convert #rrggbb to 'r, g, b' format."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join([c * 2 for c in hex_color])
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"{rgb[0]}, {rgb[1]}, {rgb[2]}"
```

Usage in template: `{{ theme.primary_color|hex_to_rgb }}`

## Admin Interface

The Wagtail admin interface is automatically generated from the model's `panels` attribute:

```python
class ThemeSettings(BaseSiteSetting):
    panels = [
        MultiFieldPanel([
            FieldRowPanel([
                NativeColorPanel("body_color_light"),
                # NativeColorPanel("body_color_dark"),  # Dark mode not supported
            ]),
            # ... more panels
        ], "Body", help_text="..."),
        # ... more MultiFieldPanels for each section
    ]
```

**Features:**

- Color pickers for all color fields
- Organized into collapsible sections
- Help text for each field
- Live preview (with page refresh)
- Revision history tracking

## Migration Path

The theme system was introduced in migration `0022_themesettings.py`. Key points:

- Initial default values match Bootstrap 5.3 defaults
- `cache_version` starts at 1
- OneToOne relationship with Site
- No data migration needed (auto-creates on first access)

## API Usage

### Programmatic Access

```python
from wagtail.models import Site
from ams.cms.models import ThemeSettings

# Get theme for specific site
site = Site.objects.get(hostname="example.com")
theme = ThemeSettings.for_site(site)

# Access colors
primary = theme.primary_color  # "#0d6efd"
# Note: Dark mode fields are currently commented out in the model
# dark_bg = theme.body_bg_dark   # Not available

# Update programmatically
theme.primary_color = "#ff0000"
theme.save()  # Auto-increments cache_version, creates revision
```

### Cache Management

```python
from django.core.cache import cache

# Manually clear cache for site
site_id = 1
version = 5
cache.delete(f"theme_version_site{site_id}")
cache.delete(f"theme_css_v{version}_site{site_id}")

# Check cache status
version = cache.get(f"theme_version_site{site_id}")
css = cache.get(f"theme_css_v{version}_site{site_id}")
```

## Testing

Key test areas (see `ams/cms/tests/test_theme.py`):

1. **Model Tests**: Creation, saving, validation, revisions
2. **CSS Generation Tests**: Template rendering, color conversion
3. **Signal Tests**: Cache clearing on save/delete
4. **Template Tag Tests**: Caching behavior, performance, edge cases

Example test:

```python
def test_template_tag_uses_two_tier_cache(site, rf):
    theme = ThemeSettings.objects.create(site=site)
    cache.clear()
    request = rf.get("/")

    # First call - should query DB
    with patch("ams.cms.templatetags.cms_tags.ThemeSettings.for_site") as mock:
        mock.return_value = theme
        template = Template("{% load cms_tags %}{% theme_css %}")
        context = RequestContext(request, {})
        output1 = template.render(context)
        assert mock.call_count == 1

    # Second call - should use cache
    with patch("ams.cms.context_processors.ThemeSettings.for_site") as mock:
        context2 = theme_settings_processor(request)
        assert mock.call_count == 0  # No DB query!
```

## Performance Optimization Tips

### For Development

- Use local memory cache (default) for simplicity
- Cache will reset on server restart (no persistence needed)

### For Production

**Recommended cache backend: Redis**

```python
# config/settings/production.py
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "ams",
    }
}
```

**Benefits:**

- Cache persists across deployments
- Shared cache in multi-server setups
- Better memory management
- Monitoring and debugging tools

### Monitoring

Track these metrics:

```python
# Add middleware to track cache performance
class ThemeCacheMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Track cache hits/misses
        cache_key = f"theme_version_site{request.site.id}"
        is_cached = cache.get(cache_key) is not None

        # Log to monitoring system
        statsd.increment("theme.cache.hit" if is_cached else "theme.cache.miss")

        return self.get_response(request)
```

## Security Considerations

1. **Custom CSS Sanitization**: The `custom_css` field allows arbitrary CSS - consider adding CSP headers
2. **Color Validation**: Enforced at form level via `ColorField`
3. **XSS Prevention**: All template variables use `|safe` only after rendering from trusted DB source
4. **Permission Control**: Only staff with Wagtail admin access can modify

## Extending the System

### Adding New Color Variables

1. Add field to model:
```python
class ThemeSettings(BaseSiteSetting):
    new_color = ColorField(default="#000000")
```

2. Add to panels:
```python
panels = [
    MultiFieldPanel([
        NativeColorPanel("new_color"),
    ], "New Section"),
]
```

3. Add to template:
```html
--bs-new-color: {{ theme.new_color }};
```

4. Create migration: `python manage.py makemigrations`

### Adding New Template Tags

```python
@register.filter
def lighten_color(hex_color, percent):
    """Lighten a hex color by percentage."""
    # Implementation
    return result
```

## Troubleshooting

### Cache Not Clearing

Check signal connection:
```python
from django.db.models.signals import post_save
from ams.cms.models import ThemeSettings

# Verify signal is connected
receivers = post_save._live_receivers(ThemeSettings)
print(f"Connected receivers: {len(receivers)}")
```

### Performance Degradation

Check cache backend:
```python
from django.core.cache import cache
from django.conf import settings

print(f"Cache backend: {settings.CACHES['default']['BACKEND']}")

# Test cache speed
import time
start = time.time()
cache.set("test", "value", 60)
cache.get("test")
print(f"Cache round-trip: {(time.time() - start) * 1000:.2f}ms")
```

### Multi-site Issues

Verify site detection:
```python
from wagtail.models import Site

def debug_site(request):
    site = Site.find_for_request(request)
    print(f"Request host: {request.get_host()}")
    print(f"Matched site: {site.hostname if site else 'None'}")
    print(f"Is default: {site.is_default_site if site else 'N/A'}")
```

## References

- [Bootstrap 5.3 CSS Variables](https://getbootstrap.com/docs/5.3/customize/css-variables/)
- [Django Caching Framework](https://docs.djangoproject.com/en/stable/topics/cache/)
- [Wagtail Site Settings](https://docs.wagtail.org/en/stable/reference/contrib/settings.html)
- [Django Signals](https://docs.djangoproject.com/en/stable/topics/signals/)
