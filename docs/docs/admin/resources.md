# Resources

The resources module is an optional feature that allows your association to publish downloadable resources on the website.

## Enabling Resources

Resources are disabled by default. To enable them, set the following environment variable in your environment configuration:

```ini
AMS_RESOURCES_ENABLED=True
```

A deployment or container restart is required after changing this setting.

## Managing Resources

Once enabled, resources are managed via the Django admin interface. To create a resource:

1. Go to **Resources → Resources** in the admin.
2. Set the **name**, **description**, and at least one author (user or entity).
3. Add one or more **components** (see below).
4. Check **Published** when the resource is ready to appear on the website.

Resources appear publicly at `/resources/` and include a listing page, detail pages, and a search page.

## Resource Components

Each resource has one or more components representing its actual content. Each component must have exactly one of the following:

- **URL** — a link to an external website, video (YouTube/Vimeo), or Google Drive file. The component type is detected automatically from the URL.
- **File** — an uploaded file. The component type is detected from the file extension and content.
- **Linked resource** — a reference to another resource in the system.

The component type (PDF, document, video, etc.) is set automatically when the component is saved — you do not need to select it manually.

## File Uploads

Uploaded files are stored privately and are never accessible via public URLs. Members access files through download links on the resource detail page. Each download link generates a short-lived authenticated URL — the file itself remains protected.

## Taxonomy: Categories and Tags

Resources can be tagged with a two-level taxonomy that you define:

1. Go to **Resources → Resource categories** and create categories (e.g. "Year Level", "Curriculum Area").
2. Within each category, add tags (e.g. "Year 9", "Digital Technologies").
3. Assign tags to resources via the **Tags** field on the resource form.

Tags appear as grouped filter facets on the search page, allowing users to filter results by category.

## Adding Resources to Menus

You can add links to resources pages via the Wagtail CMS menu system (Main Menu or Flat Menus).
Menu items pointing to `/resources/` URLs cannot be added while the resources module is disabled.
