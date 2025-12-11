# Copilot Instructions for AMS Codebase

This guide enables AI coding agents to work productively in the Association Management Software (AMS) project. It summarizes key architectural patterns, workflows, and conventions unique to this codebase.

## Architecture Overview

- **Monorepo Structure:** All major components live under `ams/` (Django app), with submodules for `billing`, `cms`, `memberships`, `forum`, `users`, and `utils`. Each submodule follows Django conventions: `models.py`, `views.py`, `admin.py`, `urls.py`, and `tests/`.
- **Configuration:** Centralized in `config/settings/` (`base.py`, `local.py`, `production.py`, `test.py`). Use these for environment-specific settings.
- **Static & Templates:** Static assets in `ams/static/`, templates in `ams/templates/` (mirrored by app domain).
- **Dockerized Development:** Use `docker-compose.yml` for local and production environments. Service definitions are in `compose/`.

## Developer Workflows

- **Run Server:** `python manage.py runserver 0.0.0.0:8000` (local dev)
- **Create Superuser:** `python manage.py createsuperuser`
- **Run Tests:** `pytest` (all tests), or `pytest ams/<app>/tests/` for app-specific tests. There is no need to create a virtual environment manually, it already exists.
- **Type Checks:** `mypy ams`
- **Coverage:** `coverage run -m pytest && coverage html` (view at `htmlcov/index.html`)
- **Translations:**
  - Extract: `docker compose -f docker-compose.yml run --rm django python manage.py makemessages --all --no-location`
  - Compile: `docker compose -f docker-compose.yml run --rm django python manage.py compilemessages`
- **Static Assets:** SASS/JS compilation via Gulp (`gulpfile.mjs`). Bootstrap customizations in `static/sass/custom_bootstrap_vars`. If SCSS files are changed, you do not need to run a workflow (such as `npm run gulp`) as this files are watched by a Node container and will automatically update and write files to `static/css/`. This Node container cannot be accessed if working in a dev container, so ask the user to check the script is working, if you cannot see the output in `static/css/`.

## Project-Specific Conventions

- **App Structure:** Each app in `ams/` is self-contained. Tests live in `tests/` subfolders, not in root.
- **Settings:** Never edit `config/settings/base.py` directly for local/prod/test changes—use the appropriate override file.
- **Email:** Local SMTP via Mailpit (`http://127.0.0.1:8025`).
- **Error Logging:** Sentry integration; set DSN in production settings.
- **Migrations:** Standard Django migrations per app.

## Integration Points

- **External Services:** Sentry (error logging), Mailpit (SMTP), Bootstrap (npm/gulp for CSS/JS).
- **Docker Compose:** Service orchestration for Django, Node, Traefik, Discourse, etc. See `compose/` for details.

## Examples

- To add a new model: create in `ams/<app>/models.py`, run `python manage.py makemigrations <app> && python manage.py migrate`.
- To add a translation: update `LANGUAGES` in `config/settings/base.py`, run `makemessages` and `compilemessages`.
- To customize Bootstrap: edit `static/sass/custom_bootstrap_vars`, then run Gulp.

## References

- See `/app/README.md` for general project info
- See `/app/locale/README.md` for translation workflow
- See `config/settings/` for environment configs
- See `compose/` for Docker service definitions
