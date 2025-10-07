# Path-Based Multi-Language Sites in Wagtail

This implementation allows you to serve completely separate content for different languages using Wagtail Sites, accessed via different URL paths on the same domain.

## How It Works

Instead of using Wagtail's translation system, we use **separate Wagtail Sites** to maintain completely independent content trees for each language. Users access these via different paths:

- **English**: `yoursite.com/en/`
- **Te Reo Māori**: `yoursite.com/mi/`

## Architecture

### 1. Custom Middleware (`ams/cms/middleware.py`)

The `PathBasedSiteMiddleware` intercepts requests and:

- Detects the language from the URL path prefix (`/en/` or `/mi/`)
- Maps it to the corresponding Wagtail Site (identified by hostname)
- Strips the prefix from the path so Wagtail can route pages correctly

### 2. Site Configuration

Two Wagtail Sites are configured with virtual hostnames:

- `en.example.com` → English content tree
- `mi.example.com` → Te Reo Māori content tree

The middleware maps URL paths to these hostnames.

### 3. URL Routing

Wagtail URLs are registered under both language prefixes:

```python
urlpatterns += [
    path("en/", include(wagtail_urls)),
    path("mi/", include(wagtail_urls)),
]
```

## Setting Up

### Initial Setup

Run the management command to create the sites:

```bash
python manage.py setup_language_sites
```

This creates:

- Two `Locale` objects (English and Te Reo Māori)
- Two `HomePage` instances (one per locale)
- Two `Site` objects with virtual hostnames

### Managing Content

1. **Access Wagtail Admin**: Navigate to `/cms/`

2. **Create Pages**: Each site has its own page tree:
   - English pages go under "English Home"
   - Te Reo Māori pages go under "Te Reo Māori Home"

3. **Site Settings**: In Wagtail Admin → Settings → Sites, you'll see:
   - **English Site** (hostname: `en.example.com`, default)
   - **Te Reo Māori Site** (hostname: `mi.example.com`)

4. **Association Settings**: The `AssociationSettings` model is site-specific, so you can have different logos, names, and settings per language.

## Advantages Over Translation

- ✅ **Complete Independence**: Each language has its own page structure
- ✅ **Separate Settings**: Different logos, footer links, etc. per language
- ✅ **No Translation Overhead**: No need to manage translation synchronization
- ✅ **Different Page Trees**: English and Te Reo Māori can have completely different navigation
- ✅ **Per-Site Customization**: Each site can have different themes, settings, etc.

## Switching Between Languages

To create a language switcher, you can:

1. **Detect Current Language**:

```python
# In a template or view
request.path.startswith('/en/')  # English
request.path.startswith('/mi/')  # Te Reo Māori
```

2. **Build Switch URLs**:

```html
<!-- In a template -->
{% if request.path.startswith '/en/' %}
    <a href="{{ request.path|replace:'/en/':'/mi/' }}">Te Reo Māori</a>
{% else %}
    <a href="{{ request.path|replace:'/mi/':'/en/' }}">English</a>
{% endif %}
```

Note: Since content is completely separate, switching languages will take users to the equivalent path in the other language tree (which may or may not exist).

## Customizing Path Prefixes

To change the path prefixes, edit `ams/cms/middleware.py`:

```python
path_to_site = {
    "/custom-en/": "en.example.com",  # Change path prefix here
    "/custom-mi/": "mi.example.com",
}
```

And update `config/urls.py`:

```python
urlpatterns += [
    path("custom-en/", include(wagtail_urls)),
    path("custom-mi/", include(wagtail_urls)),
]
```

## Adding More Languages

To add another language (e.g., Samoan):

1. **Update Middleware** (`ams/cms/middleware.py`):

```python
path_to_site = {
    "/en/": "en.example.com",
    "/mi/": "mi.example.com",
    "/sm/": "sm.example.com",  # Add new language
}
```

2. **Update URLs** (`config/urls.py`):

```python
urlpatterns += [
    path("en/", include(wagtail_urls)),
    path("mi/", include(wagtail_urls)),
    path("sm/", include(wagtail_urls)),  # Add new language
]
```

3. **Create Site** (via admin or management command):

   - Hostname: `sm.example.com`
   - Root page: New HomePage in Samoan locale

## Troubleshooting

### Pages Not Loading

- Check that the middleware is in the correct position in `MIDDLEWARE` settings
- Verify the Site hostnames match the middleware mapping
- Ensure the root pages are published

### 404 Errors

- Check that pages are published in Wagtail admin
- Verify the URL path includes the language prefix (`/en/` or `/mi/`)
- Check `wagtail.contrib.redirects` for any conflicting redirects

### Admin Access

The Wagtail admin is language-agnostic and accessible at `/cms/` regardless of the path-based sites.

## Production Configuration

In production, update `WAGTAILADMIN_BASE_URL` in settings to your actual domain:

```python
# config/settings/production.py
WAGTAILADMIN_BASE_URL = "https://yoursite.com"
```

## Notes

- Each site can have completely different page structures
- The middleware must be positioned before `CommonMiddleware` and after `SessionMiddleware`
- User authentication and memberships are shared across both sites
- Static files and media are shared across both sites
- Only CMS content and settings are separated per site
