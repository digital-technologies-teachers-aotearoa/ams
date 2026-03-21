# Feature Flags

AMS uses environment-variable-based feature flags to toggle optional modules per deployment.

## Available Flags

### `AMS_EVENTS_ENABLED`

| | |
|---|---|
| **Setting** | `EVENTS_ENABLED` |
| **Env var** | `AMS_EVENTS_ENABLED` |
| **Default** | `False` |
| **Purpose** | Enable or disable the events module |

When disabled (the default):

- Event URL patterns are not registered — requests to `/events/` return 404
- Events admin sections are hidden — no add, change, or view permissions
- Menu items with `/events/` URLs are rejected during validation

**Implementation pattern:** The env var is read in `config/settings/base.py` as a boolean setting. This setting is then checked in:

- `config/urls.py` — conditionally includes the events URL patterns
- `ams/events/admin.py` — `EventsFeatureFlagMixin` gates all admin permissions
- `ams/events/validators.py` — `patch_menu_item_clean()` validates menu item URLs (applied in `apps.py` `ready()`)

## Future Considerations

The current env-var approach is well-suited for flags that are set once per deployment and rarely change. If requirements evolve, consider these alternatives:

### Database-backed flags (e.g. Wagtail `BaseSiteSetting`)

Suitable if flags need to be toggled at runtime without redeployment, or managed by non-technical admins via a UI.

### Feature flag library (e.g. django-waffle)

Suitable if per-user, per-group, or percentage-based rollouts are needed (A/B testing, gradual feature rollouts).

### Middleware-based gating

Suitable if URL patterns need to remain registered (e.g. `reverse()` must work globally) while still blocking access at the request level.
