# Wagtail CMS

This guide covers the Wagtail CMS implementation in AMS, including architecture decisions, multi-language support, and key concepts for developers working with the content management system.

## Overview

AMS uses [Wagtail](https://wagtail.org/), a Django-based content management system, to provide flexible page management and content editing capabilities. The implementation supports multiple independent language sites sharing the same domain through path-based routing—a customization that deviates from Wagtail's default behavior to meet the project's internationalization requirements.

## Architecture

### Page Models

The CMS defines two primary page types that form the foundation of the content hierarchy:

#### HomePage

The root page for each language site, serving as the entry point to that language's content tree. Uses Wagtail's StreamField to provide flexible, customizable layouts without requiring template changes.

#### ContentPage

The standard page type for site content, supporting:

- Nested hierarchies for organizing content into sections
- Visibility controls (public or members-only access)
- Rich content composition through StreamField blocks
- Automatic slug validation to prevent conflicts with application URLs

Both page types leverage custom StreamField blocks for headings, paragraphs, images, image grids, image carousels, embeds, and multi-column layouts, providing content editors with powerful layout tools.

### Site Settings

Wagtail's settings framework is extended with two models for site-specific configuration:

#### SiteSettings

Associates a language code (e.g., 'en', 'mi') with each Wagtail Site. This is the critical mechanism enabling path-based routing, allowing the middleware to determine which site to serve based on the request's language.

#### AssociationSettings

Manages association-specific branding and identity:

- Association names (short and long forms)
- Logo and favicon images
- Logo display preferences (navbar, footer)
- Social media links (LinkedIn, Facebook)

Settings are accessible in templates through Wagtail's context processor: `{{ settings.cms.AssociationSettings.association_short_name }}`.

## Multi-Language Support

### The Problem Space

AMS required an unique approach for a multi language website, beyond the features of Wagtail.

- **Shared across all languages:** User accounts and authentication, membership records and billing, media library (images, documents), and static assets (CSS, JavaScript).
- **Language specific:** Page content and hierarchy, navigation menus, and settings (name, logo, social links, etc).

Wagtail's built-in internationalization system ties translations to shared page trees, which prevents fully divergent content structures and per-language customization.
A custom solution was required, that paired along with standard Django pages.

### Solution Design

The implementation uses path-based routing with these core principles:

- **Single domain, multiple sites**: All language sites share the same hostname and port
- **Independent content trees**: Each language has its own `HomePage` root and page hierarchy
- **Language-based resolution**: Sites are identified by `SiteSettings.language` rather than hostname
- **URL path differentiation**: Language is indicated through URL prefixes (e.g., `/en/about/`, `/mi/about/`)

#### Alternative Approaches Considered

##### Subdomain-based routing

Pattern: `en.example.com`, `mi.example.com`

Would work with Wagtail's default constraints but requires:

- Separate DNS configuration per language
- Multiple SSL certificates or wildcard certificates
- More complex deployment infrastructure
- URL patterns that don't align with content strategy preferences

##### Standard Wagtail i18n with translations

Uses Wagtail's built-in translation system but:

- Ties all languages to a shared page tree structure
- Limits ability to have different content organization per language
- Restricts per-language customization of settings and branding

### Implementation Details

#### Database Constraint Removal

The solution requires removing Wagtail's `(hostname, port)` unique constraint to allow multiple sites on the same domain. The `modify_site_hostname_constraint` management command provides safe, reversible constraint management.

##### Features

- Dynamically detects constraint name (varies by database hash)
- Validates operations before execution
- Prevents constraint restoration if duplicate sites exist
- Supports check, remove, and restore operations

##### Safety mechanisms

The command will not restore the constraint if doing so would violate uniqueness, instead prompting the developer to resolve duplicates first. This prevents accidental database errors.

#### Path-Based Site Middleware

The `PathBasedSiteMiddleware` component (in `ams/utils/middleware/site_by_path.py`) implements the routing logic.

##### Resolution process

1. Middleware receives request with `request.LANGUAGE_CODE` already set by Django's `LocaleMiddleware`
2. Queries for a Site where `SiteSettings.language` matches the language code
3. Falls back to the default site (`is_default_site=True`) if no match found
4. Sets `request.site` and `request._wagtail_site` for use by Wagtail's page routing

##### Critical ordering requirement

This middleware must be placed:

- **After** `django.middleware.locale.LocaleMiddleware` (which sets the language code)
- **Before** `django.middleware.common.CommonMiddleware` (which processes URLs)

Incorrect ordering will prevent proper site resolution.

#### Automated Site Setup

The `setup_cms` management command automates the multi-language site configuration.

##### Responsibilities

- Creates or updates Wagtail Locales for each language in `settings.LANGUAGES`
- Generates a `HomePage` for each language with the appropriate locale
- Creates or updates Site records with matching hostname and port
- Creates `SiteSettings` entries linking each site to its language
- Removes the hostname uniqueness constraint
- Designates the English site as the default fallback
- Removes orphaned sites not managed by the command

##### Characteristics

The command is idempotent—it can be run repeatedly without creating duplicates or errors. It's automatically invoked during `deploy_steps` and when generating sample data, ensuring environments are always correctly configured.

### Request Flow Example

Understanding how a request is processed helps clarify the system's behavior:

1. User navigates to `/en/about/`
2. Django's `LocaleMiddleware` extracts `'en'` from the URL and sets `request.LANGUAGE_CODE = 'en'`
3. `PathBasedSiteMiddleware` queries for a Site where `SiteSettings.language = 'en'`
4. Middleware sets `request.site` to the English site
5. Wagtail's routing system finds the `/about/` page within the English site's page tree
6. Template rendering uses the English site's `AssociationSettings` and page content

The same URL structure (`/mi/about/`) would resolve to the Māori site's `/about/` page, demonstrating complete content independence.

## Content Structure

### Page Hierarchy

The page tree structure separates languages at the root level:

- Root Page (depth=1, created by Wagtail)
    - English HomePage (depth=2, locale='en')
        - English ContentPages (depth=3+)
    - Māori HomePage (depth=2, locale='mi')
        - Māori ContentPages (depth=3+)

Each language site can develop its own structure independently. The English site might have sections like "Resources" and "Events", while the Māori site could organize content differently to suit cultural and linguistic contexts.

### Visibility Controls

ContentPage includes a visibility field controlling access:

- **Public**: Available to all visitors
- **Members only**: Requires an active membership (enforced in the page's `serve()` method)

When a user without an active membership attempts to access a members-only page, they receive an HTTP 403 Forbidden response.

### URL Validation

To prevent content pages from conflicting with Django application URLs (like `/users/`, `/billing/`, `/forum/`), ContentPage validates slugs during save. This validation only applies to direct children of HomePage—the top level where conflicts would occur. Nested pages can use any slug without restriction.

## Development Workflow

### Initial Setup

Site configuration is handled automatically. The `setup_cms` command runs as part of:

- `python manage.py sample_data` (local development data generation)
- `python manage.py deploy_steps` (production deployment)

Manual site creation or configuration is typically unnecessary unless debugging or customizing the setup.

### Content Management

#### Accessing the admin

Navigate to `/cms/` to access the Wagtail admin interface.

#### Working with multiple sites

When editing settings (Settings → Association Settings), use the site selector dropdown to switch between English and Māori sites. Each site has independent settings.

#### Creating pages

Pages are created under the appropriate language's HomePage. The Wagtail page tree clearly shows which pages belong to which language site based on their parent hierarchy.

### Configuration Requirements

#### Middleware ordering

Verify middleware configuration in `config/settings/base.py`:

```python
MIDDLEWARE = [
    # ... earlier middleware
    "django.middleware.locale.LocaleMiddleware",       # Must come first
    "ams.utils.middleware.site_by_path.PathBasedSiteMiddleware",  # Then site resolution
    "django.middleware.common.CommonMiddleware",       # Then common processing
    # ... remaining middleware
]
```

#### Environment variables

Set `WAGTAILADMIN_BASE_URL` in production settings for proper admin link generation in emails and notifications.

## Technical Considerations

### Site Identification Strategy

With the hostname constraint removed, sites are identified through a three-tier system:

1. **Primary identifier** (`SiteSettings.language`): Used for routing and site resolution
2. **Human label** (`Site.site_name`): Displayed in admin interfaces for clarity
3. **Content root** (`Site.root_page`): Determines the top of the page tree

All three must be configured correctly for each site.

### Default Site Role

One site must be designated as `is_default_site=True` (conventionally English). This site serves as:

- Fallback when language code doesn't match any site
- Default for admin interface when no site context exists
- Initial site for new deployments

### Constraint Management Commands

The hostname constraint can be inspected and modified:

```bash
# View current constraint status and check for duplicates
python manage.py modify_site_hostname_constraint --check

# Remove constraint to enable multi-language sites
python manage.py modify_site_hostname_constraint --remove

# Restore constraint (only succeeds if no duplicates exist)
python manage.py modify_site_hostname_constraint --restore
```

The restore operation performs validation and will fail with a clear error if duplicate hostname:port combinations exist, requiring manual cleanup via Django shell.

## Testing

### Middleware Test Coverage

The `PathBasedSiteMiddleware` includes comprehensive tests in `ams/utils/tests/test_site_by_path_middleware.py`:

- Language code extraction from URL paths
- Site resolution based on language
- Fallback behavior to default site
- Handling of invalid language codes
- Processing of paths without language prefixes

### Testing Best Practices

When developing CMS features:

- Test with both English and Māori sites to verify content isolation
- Verify that site settings are properly scoped
- Ensure navigation and URLs work correctly for each language
- Test fallback behavior when expected site doesn't exist

## Related Resources

### Code locations

- `ams/cms/models.py` — Page models and settings
- `ams/utils/middleware/site_by_path.py` — Site resolution middleware
- `ams/cms/management/commands/setup_cms.py` — Automated site configuration
- `ams/cms/management/commands/modify_site_hostname_constraint.py` — Constraint management
- `ams/utils/tests/test_site_by_path_middleware.py` — Middleware tests

### External documentation

- [Wagtail Settings](https://docs.wagtail.org/en/stable/reference/contrib/settings.html)
- [Wagtail Sites](https://docs.wagtail.org/en/stable/reference/pages/model_reference.html#site)
