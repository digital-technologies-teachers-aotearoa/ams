# CMS

The website uses a content management system (CMS) called Wagtail to allow editing of website content.
This includes:

- Editing page content
- Setting the association name and logo

## Admin interface

The CMS can be accessed at the `/cms/` path.

## Pages

### Reserved URL Patterns

The following URL patterns are reserved for applications and cannot be used as page slugs directly under the homepage:

- `/billing/` - Billing application
- `/users/` - User management
- `/forum/` - Forum application
- `/cms/` - Content management system
- `/accounts/` - User authentication
- `/terms/` - Terms and conditions

When creating new pages, avoid using these terms as slugs for pages that are direct children of the homepage to prevent URL conflicts.

### Menus

When creating menus within the CMS, you may want to link to a page that is not created in the CMS, but a different part of the website.
You can use the following URLs within the 'External URL' field on a menu item to link to the following pages:

- Discourse forum = `/forum/` - This will automatically redirect visitors to the forum with proper authentication.
- Terms and Conditions = `/terms/` - This displays all current terms and policies.
