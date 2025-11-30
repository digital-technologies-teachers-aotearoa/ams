# Management Commands Catalog

This catalog lists AMS-specific Django management commands with descriptions, arguments, and usage. Run commands from the project root using `python manage.py <command>`.

## `setup_cms`

Sets up the CMS for multi-language path-based sites. Ensures the root page exists, creates/updates Wagtail Locales and a language-specific `HomePage` for each language in `settings.LANGUAGES`, and creates/updates corresponding `Site` records on the configured domain/port. It also removes the Wagtail `(hostname, port)` uniqueness constraint to allow multiple sites on one hostname and outputs a friendly summary of the generated site URLs.

- Arguments: none.
- Notes: Reads languages and domain/port from settings; idempotent for existing sites/pages.

## `sample_data`

Seeds a non-production database with realistic sample content for development: migrates the database, reloads initial Wagtail data, creates sample admin and user accounts, sample membership options, and runs `setup_cms` to ensure CMS pages and sites are ready. Intended for local dev; guarded from running in deployed environments.

- Arguments: none.
- Safety: Errors if `settings.DEPLOYED` is true.
- Example:

  ```bash
  python manage.py sample_data
  ```

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
