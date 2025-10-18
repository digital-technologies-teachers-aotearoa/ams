# URLs

The AMS project has a combination of prefined URL routes (static pages), and dynamic pages created within the Wagtail CMS.
Therefore specific URLs namespaces are reserved for static pages.

- `/billing/*` - Billing application
- `/users/*` - Users application
- `/users/membership/*` - Membership application
    - This is placed within the `users` namespace to allow the CMS to have a `membership` page.

!!! example "Alternative approach"

    Alternatively, all Wagtail pages could be under a `/pages/` subdirectory, preventing any issues with reserved URL slugs.
    However this would require an override for the homepage to display at the base URL.
