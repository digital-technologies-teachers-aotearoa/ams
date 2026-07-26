# Management Commands Catalog

This catalog lists AMS-specific Django management commands with descriptions, arguments, and usage. Run commands from the project root using `python manage.py <command>`.

## `setup_cms`

Sets up the CMS for multi-language path-based sites. Ensures the root page exists, creates/updates Wagtail Locales and a language-specific `HomePage` for each language in `settings.LANGUAGES`, and creates/updates corresponding `Site` records on the configured domain/port. It also removes the Wagtail `(hostname, port)` uniqueness constraint to allow multiple sites on one hostname and outputs a friendly summary of the generated site URLs.

- Arguments: none.
- Notes: Reads languages and domain/port from settings; idempotent for existing sites/pages.

## `sample_data`

Seeds a non-production database with realistic sample content for development: migrates the database, then runs (in order) `create_sample_admin`, `create_sample_users`, `create_sample_profile_questions`, `create_sample_membership_options`, `setup_cms`, `create_sample_cms_content`, `create_sample_events`, and `create_sample_resources`, and finally sets `AssociationSettings` for every site. Each sub-command below can also be run standalone once the database is migrated. Intended for local dev; guarded from running in deployed environments.

- Arguments: none.
- Safety: Errors if `settings.DEPLOYED` is true.
- Example:

  ```bash
  python manage.py sample_data
  ```

### Sample data sub-commands

Each of these is normally invoked by `sample_data` above, not run directly — listed here so they're not undocumented. None take arguments.

- `create_sample_admin` — creates (or promotes) a superuser at `settings.SAMPLE_DATA_ADMIN_EMAIL`/`SAMPLE_DATA_ADMIN_PASSWORD` (see `.envs/.local/django.ini`), with a verified allauth email address.
- `create_sample_users` — creates a set of sample non-admin user accounts.
- `create_sample_profile_questions` — creates sample membership profile questions.
- `create_sample_membership_options` — creates sample membership options/pricing.
- `create_sample_cms_content` — creates sample CMS pages (About, Team, Members Only, an articles index and articles), homepage StreamField content demonstrating every block type, and main/footer navigation menus, for each configured language site.
- `create_sample_events` — creates sample regions, locations, series, entities, and a spread of past/future events with sessions, for the [events module](../website/reference/events.md).
- `create_sample_resources` — creates sample resource categories, tags, and resources, for the [resources module](../website/reference/resources.md).
- `create_sample_terms` — creates sample `Term`/`TermVersion` records. Not called by `sample_data` — run standalone if terms/conditions data is needed.

## `ensure_wagtail_root`

Recreates Wagtail's default `Locale`, root `Page`, and root `Collection` if missing, along with the `access_admin` permission grants on the Moderators/Editors groups. Needed because `manage.py flush` truncates data without replaying the data migrations that normally create these rows, which would otherwise break `setup_cms` and prevent sign-in to `/cms/` on a flushed-and-recovered dev database.

- Arguments: none.
- Notes: Idempotent — checks for each row/grant before creating it.

## `modify_site_hostname_constraint`

Manages the database constraint that enforces unique `(hostname, port)` on Wagtail Sites. Use this to remove the constraint when running multiple path-based sites under a single hostname, check current status and duplicates, or restore the constraint when needed. The command auto-detects the actual constraint name, provides safety checks, and prints a clear status report.

- Arguments:
    - `--remove`: drop the unique constraint to allow duplicate hostname:port.
    - `--restore`: re-add the unique constraint (blocked if duplicates exist).
    - `--check`: show current status and duplicates.
- Example:

  ```bash
  python manage.py modify_site_hostname_constraint --check
  ```

## `deploy_steps`

Runs essential deployment-time actions in sequence to bring the application up-to-date after a release. Currently performs a non-interactive database migration followed by `setup_cms` to ensure language-specific sites and pages exist and are correctly configured.

- Behavior: Executes `migrate` (non-interactive) then `setup_cms`.
- Arguments: none.

## `fetch_invoice_updates`

Fetches and applies the latest Xero invoice data for any local `Invoice` marked `update_needed=True`, as a fallback for missed Xero webhooks. Only acts when `XeroBillingService` is configured — a no-op under mock billing, and an error if no billing service is configured. See [Billing integration](billing.md#fetch_invoice_updates) for full behaviour (batch size, scheduling).

- Arguments: none.
- Example:

  ```bash
  python manage.py fetch_invoice_updates
  ```

## `check_settings_glossary`

Verifies every client-decidable `AMS_*` setting in `config/settings/base.py` has exactly one entry in the [settings glossary](../getting-started/settings-glossary.md), and vice versa, and that none of them are duplicated in [Deployment](deployment.md)'s environment variable table. Fails loudly (non-zero exit) if the glossary has drifted from the code. Runs in CI on every PR — see [Documentation conventions](docs-conventions.md#settings-glossary-anti-drift-check).

- Arguments: none.
- Example:

  ```bash
  python manage.py check_settings_glossary
  ```
