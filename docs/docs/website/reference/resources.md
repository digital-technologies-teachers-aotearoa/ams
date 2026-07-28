# Resources

The resources module is an optional feature that allows your association to publish downloadable resources on the website.

## Enabling Resources

Whether resources are switched on is a decision made during onboarding — see [question 5 of the decision questionnaire](../../getting-started/decision-questionnaire.md#5-optional-features) and the [`AMS_RESOURCES_ENABLED`](../../getting-started/settings-glossary.md#ams_resources_enabled) settings glossary entry.

This isn't something you configure yourself: your provider switches it on when your site is set up (see [provisioning runbook: environment settings](../../hosting/provisioning-runbook.md#4-environment-settings)).
If you don't see **Resources** in the Django admin, ask your provider to turn it on. For the technical detail of what the flag does, see [feature flags: `AMS_RESOURCES_ENABLED`](../../developer/feature-flags.md#ams_resources_enabled).

## Managing Resources

Once enabled, resources are managed via the Django admin interface. To create a resource:

1. Go to **Resources → Resources** in the admin.
2. Set the **name**, **description**, and at least one author (user or entity).
3. Set **Visibility** (see [Who can see a resource](#who-can-see-a-resource) below).
4. Add one or more **components** (see below).
5. Check **Published** when the resource is ready to appear on the website.

Resources appear publicly at `/resources/` and include a listing page, detail pages, and a search page.

## Resource Components

Each resource has one or more components representing its actual content. Each component must have exactly one of the following:

- **URL** — a link to an external website, video (YouTube/Vimeo), or Google Drive file. The component type is detected automatically from the URL.
- **File** — an uploaded file. The component type is detected from the file extension and content.
- **Linked resource** — a reference to another resource in the system.

The component type (PDF, document, video, etc.) is set automatically when the component is saved — you do not need to select it manually.

## File Uploads

Uploaded files are stored privately and are never accessible via public URLs. Members access files through download links on the resource detail page. Each download link generates a short-lived authenticated URL — the file itself remains protected.

## Who can see a resource

The **Visibility** field controls both whether a resource is listed at all, and whether its components can actually be opened or downloaded:

| Visibility | Who can see it listed | Who can open its components |
| --- | --- | --- |
| Public | Everyone | Everyone |
| Account required to access | Everyone | Anyone signed in |
| Membership required to access | Everyone | Members only |
| Members only | Members only | Members only |

Most associations only need **Public** and **Members only** — the two middle options exist for the less common case of wanting a resource visible to everyone, but its actual content restricted.

## Taxonomy: Categories and Tags

Resources can be tagged with a two-level taxonomy that you define:

1. Go to **Resources → Resource categories** and create categories (e.g. "Year Level", "Curriculum Area").
2. Within each category, add tags (e.g. "Year 9", "Digital Technologies").
3. Assign tags to resources via the **Tags** field on the resource form.

Tags appear as grouped filter facets on the search page, allowing users to filter results by category.

## Adding Resources to Menus

You can add links to resources pages via the Wagtail CMS menu system (Main Menu or Flat Menus).
Menu items pointing to `/resources/` URLs cannot be added while the resources module is disabled.

See [Tutorial 10: Resources](../setup/resources.md) for a step-by-step walkthrough of adding a resource.
