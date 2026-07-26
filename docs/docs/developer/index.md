# Developing AMS

This section covers contributing to and deploying the AMS codebase itself.

## Where to start

1. [Contributing](contributing.md) — local development setup (Dev Containers, common commands).
2. [Documentation conventions](docs-conventions.md) — if you're changing UI these docs cover, or writing docs yourself.
3. [Deployment](deployment.md) — deploying the AMS Docker image on any platform.
4. Then the per-topic pages below, as your work needs them.

## App map

AMS is a Django project; its apps live under `ams/`:

- `users` — accounts, authentication, and profiles.
- `organisations` — associations and their settings.
- `memberships` — membership types, applications, and approval.
- `billing` — pluggable billing provider integration (Xero shipped today).
- `cms` — the Wagtail content-management system: page types, menus, theming.
- `events` — the optional events feature.
- `resources` — the optional resources (downloadable file) feature.
- `forum` — Discourse forum integration and SSO sync.
- `terms` — terms and conditions acceptance tracking.
- `entities` — shared organisational entities used by events.
- `utils` — cross-app helpers (permissions, error handlers, crispy-forms helpers).

The rest of this section's pages, listed in the sidebar, cover one topic each: feature flags, resources, billing, management commands, forum, icons, URLs, permission caching, the AMS project's own dev site, Wagtail CMS, theming, and email templates.
