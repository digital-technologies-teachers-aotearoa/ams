# Events

**Who this page is for:** client website admins — the volunteers who run the day-to-day site once it's launched.

The events module is an optional feature that allows your association to publish and manage events on the website.

## Enabling events

Whether events are switched on is a decision made during onboarding — see [question 5 of the decision questionnaire](../../getting-started/decision-questionnaire.md#5-optional-features) and the [`AMS_EVENTS_ENABLED`](../../getting-started/settings-glossary.md#ams_events_enabled) settings glossary entry.

This isn't something you configure yourself: your provider switches it on when your site is set up (see [provisioning runbook: environment settings](../../hosting/provisioning-runbook.md#4-environment-settings)).
If you don't see **Events** in the Django admin, ask your provider to turn it on.
For the technical detail of what the flag does, see [feature flags: `AMS_EVENTS_ENABLED`](../../developer/feature-flags.md#ams_events_enabled).

## Managing events

Once enabled, events are managed via the Django admin interface. You can create and manage:

- **Events** — individual events with sessions, locations, and registration details
- **Series** — group related events together
- **Locations** — venues with optional map coordinates
- **Regions** — geographical groupings for locations

Events appear publicly at `/events/` and include pages for upcoming events, past events, and individual event details.

## Adding events to menus

You can add links to events pages via the Wagtail CMS menu system (Main Menu or Flat Menus).
Menu items pointing to `/events/` URLs cannot be added while the events module is disabled.

See [Tutorial 9: Events](../setup/events.md) for a step-by-step walkthrough of adding a location and an event.
