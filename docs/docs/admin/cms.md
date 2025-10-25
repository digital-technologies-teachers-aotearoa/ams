# Content management

The website uses a content management system (CMS) called Wagtail to allow editing of website content.
This includes:

- Editing page content
- Setting the association name and logo

## Admin interface

The CMS can be accessed at the `/cms/` path.

## Quick Links and Reserved URLs

### Forum Links

To create a link to the forum in your content, use `/forum/` as the URL.
This will automatically redirect visitors to the forum with proper authentication.

### Reserved URL Patterns

The following URL patterns are reserved for applications and cannot be used as page slugs directly under the homepage:

- `/billing/` - Billing application
- `/users/` - User management
- `/forum/` - Forum application
- `/cms/` - Content management system
- `/accounts/` - User authentication

When creating new pages, avoid using these terms as slugs for pages that are direct children of the homepage to prevent URL conflicts.
