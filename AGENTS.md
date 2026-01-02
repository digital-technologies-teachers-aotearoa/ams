# AI Instructions for AMS Codebase

This guide enables AI coding agents to work productively in the Association Management Software (AMS) project.

## Critical Rules

**IMPORTANT:** Before writing ANY code, YOU MUST:

1. Read ALL relevant files first - NEVER propose changes to code you haven't read
2. Understand the existing architecture and patterns
3. Ask clarifying questions if ANY context is missing or ambiguous. Use the askquestion tool to clarify requirements.
4. Wait for answers before proceeding

**YOU MUST NOT:**

- Make assumptions to fill missing information
- Invent APIs, libraries, or project structure
- Guess missing requirements
- Write code before understanding the full context

## Architecture

**Django Structure:**

- All apps under `ams/`: `billing`, `cms`, `memberships`, `forum`, `users`, `organisations`, `utils`
- Each app follows Django conventions: `models.py`, `views.py`, `admin.py`, `urls.py`, `tests/`

**Configuration:**

- Settings in `config/settings/`: `base.py`, `local.py`, `production.py`, `test.py`
- **NEVER** edit `base.py` for environment-specific changes - use override files

**Key Locations:**

- Static assets: `ams/static/`
- Templates: `ams/templates/` (organized by app)
- Documentation: `docs/docs/`

## Running Commands

**IMPORTANT:** This is a Dockerized project. ALL commands run inside Docker containers.

### Command Patterns

**For long-running processes (server, shell, tests):**

```bash
docker-compose exec django <command>
```

**For one-time operations (migrations, createsuperuser):**

```bash
docker compose -f docker-compose.yml run --rm django <command>
```

### Essential Commands

| Task             | Command                                                                                     |
| ---------------- | ------------------------------------------------------------------------------------------- |
| Run server       | `docker-compose exec django python manage.py runserver 0.0.0.0:8000`                        |
| Run tests        | `docker-compose exec django pytest` or `docker-compose exec django pytest ams/<app>/tests/` |
| Django shell     | `docker-compose exec django python manage.py shell`                                         |
| Make migrations  | `docker compose run --rm django python manage.py makemigrations <app>`                      |
| Run migrations   | `docker-compose exec django python manage.py migrate`                                       |
| Create superuser | `docker compose run --rm django python manage.py createsuperuser`                           |
| View logs        | `docker-compose logs -f django`                                                             |
| Restart service  | `docker-compose restart <service>`                                                          |

**IMPORTANT:**

- No need to `cd /app` - terminal defaults there
- Virtual environment already exists - don't create one
- For debugging, use Django shell to load valid settings

## Step-by-Step Workflow for Code Changes

When making changes, follow this sequence:

### 1. Understanding Phase

1. Read all relevant files using Read tool
2. Search for similar patterns in the codebase
3. Check for existing helper functions (see Helper Functions section)
4. Review related tests

### 2. Planning Phase

1. Identify what files need changes
2. Check if helper functions exist for your use case
3. Verify you understand the data flow
4. Ask questions if anything is unclear

### 3. Implementation Phase

1. Make minimal changes - avoid over-engineering
2. Follow existing patterns in the codebase
3. Use helper functions instead of duplicating logic
4. Only add what was requested - no extra features

### 4. Testing Phase

1. Run affected tests: `docker-compose exec django pytest ams/<app>/tests/`
2. Run type checks if modifying Python: `docker-compose exec django mypy ams`
3. Verify changes work as expected

### 5. Migration Phase (if models changed)

1. Create migration: `docker compose run --rm django python manage.py makemigrations <app>`
2. Run migration: `docker-compose exec django python manage.py migrate`
3. Test migration is reversible if needed

## Helper Functions - ALWAYS Check These First

**YOU MUST check if these exist before writing similar logic:**

### Permission Checking

```python
from ams.utils.permissions import user_has_active_membership

# Use this for checking active memberships (5-min cache)
if user_has_active_membership(request.user):
    # User has access

# Use this for per-request caching (fresher data)
from ams.utils.permissions import user_has_active_membership_request_cached
```

### Crispy Forms Cancel Button

```python
from ams.utils.crispy_forms import Cancel

# In your FormHelper layout:
Cancel(url=reverse('app:view_name'))  # Custom URL
Cancel()  # Defaults to root_redirect
```

### Billing Service

```python
from ams.billing.services.base import get_billing_service

billing_service = get_billing_service()  # Returns None if not configured
if billing_service:
    billing_service.update_user_billing_details(user)
```

### Custom Error Handlers

Available in `ams/utils/views.py`:

- `bad_request()`, `permission_denied()`, `server_error()`, `page_not_found()`

## Coding Conventions

### MUST Follow

1. **Forms:** Use crispy forms with FormHelper in form class
2. **Tests:** Place in `tests/` subfolder, NOT in app root
3. **Settings:** Use appropriate override file for environment-specific settings
4. **Migrations:** One migration per app, use descriptive names
5. **Auth:** Use `User = get_user_model()"` (NOT "ams.users.User")
6. **Imports:** Imports only can occur at the top of a file.

### NEVER Do

1. **DON'T** over-engineer - make minimal changes only
2. **DON'T** add features beyond what was requested
3. **DON'T** add comments/docstrings to code you didn't change
4. **DON'T** add error handling for scenarios that can't happen
5. **DON'T** create abstractions for one-time operations
6. **DON'T** skip reading files before modifying them
7. **DON'T** run commands without the Docker wrapper

### Static Assets & Translations

**Static Assets:**

- Edit SCSS in `static/sass/custom_bootstrap_vars`
- Node container auto-compiles (no manual Gulp needed)
- If changes don't appear, ask user to verify Node container is running

**Translations:**

```bash
# Extract messages
docker compose run --rm django python manage.py makemessages --all --no-location

# Compile messages
docker compose run --rm django python manage.py compilemessages
```

**IMPORTANT:** Update `LANGUAGES` in `config/settings/base.py` before adding new languages

## Management Commands

Common commands in `ams/*/management/commands/`:

- `sample_data` - Generate development data
- `deploy_steps` - Run deployment steps
- `setup_cms` - Set up Wagtail CMS
- `fetch_invoice_updates` - Sync billing invoices
- `create_sample_admin` - Create sample admin user

Run with: `docker-compose exec django python manage.py <command_name>`

## Integration Points

- **Email (local):** Mailpit at `http://127.0.0.1:8025`
- **Error logging:** Sentry (production)
- **CSS/JS:** Bootstrap via npm/Gulp
- **Site routing:** `PathBasedSiteMiddleware` for multi-language Wagtail sites

## Output Formatting Requirements

When presenting code changes:

1. **State what you're doing** before doing it
2. **Show the specific change** you're making
3. **Reference file locations** with `path:line` format when helpful
4. **Explain WHY** for non-obvious changes
5. **List next steps** if the task isn't complete

## Common Patterns

### Adding a New Model

1. Create model in `ams/<app>/models.py`
2. Run: `docker compose run --rm django python manage.py makemigrations <app>`
3. Run: `docker-compose exec django python manage.py migrate`
4. Add to admin.py if needed
5. Write tests in `ams/<app>/tests/`

### Adding a New View

1. Read existing views in `ams/<app>/views.py`
2. Check if mixins exist in `ams/utils/` or `ams/<app>/mixins.py`
3. Add view following existing patterns
4. Add URL to `ams/<app>/urls.py`
5. Create template in `ams/templates/<app>/`
6. Write tests

### Adding a Form

1. Create in `ams/<app>/forms.py`
2. Add FormHelper with crispy forms layout
3. Use Cancel() helper for cancel button
4. Import in `views.py`
5. Create template using {% crispy form %}

## References

- General info: `/app/README.md`
- Translation workflow: `/app/locale/README.md`
- Environment configs: `config/settings/`
- Docker services: `compose/`
- Developer docs: `docs/docs/developer/`

## Final Reminders

**ALWAYS:**

- Read before writing
- Use existing helpers
- Follow existing patterns
- Test your changes
- Be minimal and focused

**NEVER:**

- Assume or guess
- Over-engineer
- Skip reading files
- Forget Docker wrappers
- Invent APIs or structure
