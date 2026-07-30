# Resources

The resources module is an optional feature that allows your association to publish downloadable resources on the website. Resources are managed via the Django admin and browsed publicly. File downloads are served through private, authenticated URLs — files are never exposed via public hotlinks.

For the client-facing view of this feature, see the [admin guide: Resources](../website/reference/resources.md).

## Configuration

| | |
| --- | --- |
| **Setting** | `RESOURCES_ENABLED` |
| **Env var** | `AMS_RESOURCES_ENABLED` |
| **Default** | `False` |
| **Purpose** | Enable or disable the resources module |

Set the env var in your environment configuration and restart the container. See [Feature Flags](feature-flags.md) for the full flag behaviour.

## Models

### ResourceCategory and ResourceTag

A two-level, admin-managed taxonomy. Administrators define categories (e.g. "Year Level", "Curriculum Area") and tags within each category (e.g. "Year 9", "Digital Technologies"). Tags have an optional `abbreviation` and `color` for display customisation.

- `(category, slug)` is unique — two categories can have tags with the same name without conflict.
- `order` controls display order within a category.

### Resource

| Field | Type | Notes |
| --- | --- | --- |
| `name` | `CharField(200)` | |
| `slug` | `AutoSlugField` | Always updated from name |
| `description` | `HTMLField` | TinyMCE rich text |
| `published` | `BooleanField` | Controls public visibility |
| `author_users` | `M2M(User)` | At least one author required |
| `author_entities` | `M2M(Entity)` | At least one author required |
| `tags` | `M2M(ResourceTag)` | Optional taxonomy tags |
| `search_vector_en` | `SearchVectorField` | Maintained by Postgres trigger; not editable |
| `search_vector_mi` | `SearchVectorField` | Maintained by Postgres trigger; not editable |
| `view_count` | `PositiveIntegerField` | Denormalised count, not editable — see [View tracking](#view-tracking) |

`name` and `description` are translated fields (via `django-modeltranslation`), backed by `name_en`/`name_mi` and `description_en`/`description_mi` columns. `search_vector_en` and `search_vector_mi` are each updated by a Postgres trigger on `INSERT OR UPDATE OF name_en, description_en, name_mi, description_mi`. Weights: `name` = A, `description` and component names = B, tag names/abbreviations and author names = C. `search_vector_en` indexes the English columns with the `english` text-search config; `search_vector_mi` indexes the Māori columns with the `simple` config, falling back to the English value for any field left blank in Māori. The trigger functions are defined in migration `0016` (a single combined `search_vector` column, populated by migrations `0002`, `0003`, and `0005`, was split into these two per-language columns) — no application-level signals are used.

### ResourceComponent

Each resource has one or more components representing its actual content. Exactly one of three mutually exclusive data fields must be set:

| Field | Meaning |
| --- | --- |
| `component_url` | Link to an external website, video, or Google Drive file |
| `component_file` | Uploaded file, stored in private blob storage |
| `component_resource` | Link to another Resource (recursive reference) |

`component_type` is derived automatically in `save()` via `file_types.detect_url_type()` or `file_types.detect_file_type()` — it is never set manually. Supported types include PDF, document, spreadsheet, slideshow, image, video, audio, archive, and website.

`clean()` enforces the single-data-field constraint and prevents a component from referencing its own parent resource.

## Private file storage

`component_file` uses `PrivateMediaStorage` (`config/storage_backends.py`), which is an S3 backend with `querystring_auth=True` and a private ACL. Files are never publicly accessible.

Every component click — file, external URL, or linked resource — is routed exclusively through `ResourceComponentAccessView` (`urls.py` names: `component_access`, and `component_download` as an alias kept for backwards compatibility):

1. Confirms the component exists and its parent resource is published.
2. Confirms the requesting user can access the resource (per its visibility level).
3. Redirects to whichever of `component_file.url` (a short-lived presigned S3 URL), `component_url`, or `component_resource.get_absolute_url()` is set, and records a view.

Never expose `component_file.url` or `component_url` directly in templates — always use the `component_access` URL name.

**Open-redirect surface.** `component_url` is admin-entered and stored, not user-supplied per request, so this isn't an open redirect in the classic sense — but the view does emit a 302 to whatever URL is stored. There is deliberately no allowlist or `url_has_allowed_host_and_scheme`-style validation; admins are trusted to enter sane URLs, the same way they're trusted with any other free-text admin field.

## View tracking

`ResourceView` and `ResourceComponentView` are append-only event tables (`resource`/`component` FK, `datetime_viewed`, indexed together for time-windowed queries) recording every view with no dedup and no user/IP — identity is never stored, by design. `Resource.view_count` and `ResourceComponent.view_count` are denormalised counters kept in sync by `record_resource_view()` / `record_component_view()` in `models.py`.

Both helpers use `queryset.update(view_count=F("view_count") + 1)`, never `obj.view_count += 1; obj.save()` — the latter would lose concurrent increments and, on `Resource`, would also bump `datetime_updated` (`auto_now=True`), corrupting the home page's `-datetime_updated`-adjacent ordering assumptions.

`ResourceDetailView.get_context_data()` calls `record_resource_view()` after `get_object()` has already enforced the visibility check, so a `PermissionDenied` never counts. `RedirectToCosmeticURLMixin` returns its redirect before `get_context_data()` runs, so a hit on the bare `/resource/<pk>/` URL is not counted — only the follow-up request to the canonical slug URL is.

**Pruning.** `prune_resource_views` deletes `ResourceView`/`ResourceComponentView` rows older than `settings.RESOURCE_VIEW_RETENTION_DAYS` (default 400; override in a settings file, not an env var — this isn't a per-client decision). `view_count` totals are untouched by pruning. The command is not scheduled anywhere yet — run it manually (`docker compose exec django python manage.py prune_resource_views`) or wire it into a scheduled job once view volume justifies it.

## Full-text search

Search is powered by Postgres native full-text search with no application-level signals, scoped to the active UI language.

**Search vector maintenance:** see [Models: Resource](#resource) above for how `search_vector_en`/`search_vector_mi` are kept current. Related content (component names, author names, tag names/abbreviations) is handled by additional triggers on those related tables, all defined alongside the resource triggers in migration `0016`.

**`ResourceSearchView`** accepts a `q` query parameter and optional `tag` parameters:

- If `q` is given, picks `search_vector_en` (config `english`) or `search_vector_mi` (config `simple`) based on `django.utils.translation.get_language()` (defaulting to English for any other language), filters on that column with `@@`, annotates `SearchRank`, and orders by `-rank`.
- `SearchQuery` uses `search_type="websearch"`, supporting quoted phrases, `-excluded` terms, and `OR`.
- Tag filtering applies OR semantics within a category and AND semantics across categories, and is ANDed with the `q` filter when both are given.

## Admin integration

- `ResourceAdmin` — fieldsets for General, Ownership, and Visibility; `filter_horizontal` for author M2Ms and tags; `ResourceComponentInline` for managing components inline.
- `ResourceCategoryAdmin` — inline `ResourceTagInline` for managing tags within a category.
- `ResourceForm` — validates that at least one author (user or entity) is present.
- All resource admin classes use `ResourcesFeatureFlagMixin` to hide permissions when the module is disabled.
