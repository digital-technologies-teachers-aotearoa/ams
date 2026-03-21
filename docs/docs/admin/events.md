# Events

The events module is an optional feature that allows your association to publish and manage events on the website.

## Enabling Events

Events are disabled by default. To enable them, set the following environment variable in your environment configuration:

```ini
AMS_EVENTS_ENABLED=True
```

A deployment or container restart is required after changing this setting.

## Managing Events

Once enabled, events are managed via the Django admin interface. You can create and manage:

- **Events** — individual events with sessions, locations, and registration details
- **Series** — group related events together
- **Locations** — venues with optional map coordinates
- **Regions** — geographical groupings for locations

Events appear publicly at `/events/` and include pages for upcoming events, past events, and individual event details.

## Adding Events to Menus

You can add links to events pages via the Wagtail CMS menu system (Main Menu or Flat Menus).
Menu items pointing to `/events/` URLs cannot be added while the events module is disabled.
