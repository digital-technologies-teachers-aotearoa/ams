# Email Templates with MJML

This project uses MJML for creating responsive, email-client-compatible HTML emails.

## Architecture Overview

The email system follows a build-time compilation approach:

1. **Design**: Email layouts are created using MJML templates
2. **Build**: MJML templates are compiled to HTML at build time
3. **Runtime**: Django renders dynamic data into the compiled HTML templates
4. **Send**: Django sends the final email using the standard email backend

This architecture provides:

- Strong email client compatibility (including Outlook)
- Fast email sending (no runtime compilation)
- Clean separation of concerns
- Easy testing
- No runtime Node.js dependency

## Directory Structure

```text
ams/
├── email_templates/           # MJML source templates (design-time)
│   ├── organisation_invite.mjml
│   └── _base.mjml            # Reusable base template
└── templates/
    └── emails/               # Compiled HTML templates (runtime)
        ├── organisation_invite.html  # HTML auto-generated from MJML
        └── organisation_invite.txt   # TXT auto-generated from html2text
```

## Creating Email Templates

### 1. Create MJML Template

Create a new `.mjml` file in `ams/email_templates/`:

```xml
<mjml>
  <mj-head>
    <mj-title>{% trans "Email Subject" %}</mj-title>
    <mj-preview>{{ preview_text }}</mj-preview>
    <mj-attributes>
      <mj-all font-family="Arial, sans-serif" />
      <mj-text font-size="16px" color="#333333" />
    </mj-attributes>
  </mj-head>
  <mj-body background-color="#f8f9fa">
    <mj-section background-color="#ffffff" padding="20px">
      <mj-column>
        <mj-text font-size="24px" font-weight="bold">
          Hello {{ user.first_name }}!
        </mj-text>
        <mj-text>
          {% trans "This is a sample email." %}
        </mj-text>
        <mj-button background-color="#0056b3" href="{{ action_url }}">
          {% trans "Click Here" %}
        </mj-button>
      </mj-column>
    </mj-section>
  </mj-body>
</mjml>
```

**Important notes:**

- Use Django template tags and variables freely - they will be preserved
- The `{% load i18n %}` tag is automatically prepended during compilation
- Use MJML components for layout, Django tags for dynamic content
- Compiled templates are excluded from djlint in the project config

### 2. Create Plain Text Version (Optional)

**Plaintext templates are now optional!** If you don't create a `.txt` file, the plaintext version will be automatically generated from the HTML using html2text.

For most emails, auto-generation works great. Only create a custom `.txt` template when you need precise control over the plaintext formatting.

If you do want a custom `.txt` file, create it in `ams/templates/emails/`:

```text
{% load i18n %}
{% trans "EMAIL SUBJECT" %}

Hello {{ user.first_name }}!

{% trans "This is a sample email." %}

{% trans "Click here:" %} {{ action_url }}
```

**When to create custom .txt templates:**

- When auto-generated formatting isn't quite right
- For critical transactional emails where you want explicit control
- When you need different content structure in plaintext vs HTML

### 3. Compile MJML to HTML

In development, the node container watches for changes:

```bash
# Compilation happens automatically when you save .mjml files
# Or manually trigger compilation:
docker compose exec node npx gulp mjml
```

For production, compilation happens automatically during the build process.

### 4. Send Email Using Django Service

Use the `send_templated_email` utility function:

```python
from ams.utils.email import send_templated_email

send_templated_email(
    subject="Welcome to AMS",
    template_name="welcome_email",  # Without .html/.txt extension
    context={
        "user": user,
        "action_url": "https://example.com/verify",
    },
    recipient_list=[user.email],
)
```

## MJML Resources

- [MJML Documentation](https://documentation.mjml.io/)
- [MJML Components](https://documentation.mjml.io/#components)
- [MJML Try it Live](https://mjml.io/try-it-live)

## Configuration

### Plaintext Generation Settings

The email system includes settings to control how plaintext is auto-generated from HTML:

```python
# In config/settings/base.py
EMAIL_PLAINTEXT_IGNORE_LINKS = False  # Include link URLs in plaintext
EMAIL_PLAINTEXT_BODY_WIDTH = 78  # Characters per line
```

**EMAIL_PLAINTEXT_IGNORE_LINKS** (Default: `False`)

- If `False`, URLs are included in the plaintext (e.g., `Click Here: https://example.com`)
- If `True`, only link text is shown without URLs

**EMAIL_PLAINTEXT_BODY_WIDTH** (Default: `78`)

- Maximum characters per line in generated plaintext
- Standard email width is 78 characters
- Adjust if you need narrower or wider lines

These settings only affect auto-generated plaintext. Custom `.txt` templates are rendered as-is.

## Development Workflow

### Local Development

1. Edit MJML files in `ams/email_templates/`
2. The node container automatically compiles them to `ams/templates/emails/`
3. (Optional) Create/update corresponding `.txt` templates if you need custom plaintext formatting
4. Use the `send_templated_email` function in your views/signals
5. Test emails appear in Mailpit at `http://localhost:8025`

### Running Tests

```bash
# Test email functionality
docker compose exec django pytest ams/utils/tests/test_email.py

# Test email content in your app
docker compose exec django pytest ams/yourapp/tests/test_emails.py
```

### Production Build

The production Docker build automatically:

1. Installs npm dependencies (including MJML)
2. Runs `npm run build` which executes `gulp build`
3. Compiles all MJML templates to HTML
4. Includes compiled templates in the final image

## Dynamic Content Rules

### Allowed

- Text content: `{{ user.name }}`
- URLs and tokens: `{{ verification_url }}`
- Translation tags: `{% trans "Text" %}`
- Conditional blocks: `{% if condition %}...{% endif %}`
- Loops: `{% for item in items %}...{% endfor %}`

### Not Allowed

- Runtime changes to layout or structure
- Dynamic MJML components

**Rule of thumb**: If layout needs to change, create a separate template.

## Best Practices

### Template Organization

- Use descriptive names: `organisation_invite.mjml`, `password_reset.mjml`
- Create base templates for shared layouts (prefix with `_`)
- Keep templates focused on a single email type

### Styling

- Use MJML components for responsive layout
- Define common styles in `<mj-attributes>`
- Keep inline styles minimal - let MJML handle it
- Test in multiple email clients (use Mailpit for local testing)

### Performance

- Avoid overly complex templates
- Keep email size reasonable (< 100KB)
- Minimize use of images

### Testing

- Always test both HTML and text versions
- Test with real context data
- Verify translation strings work correctly
- Check that links and buttons render properly

## Email Service API

### `send_templated_email()`

```python
def send_templated_email(
    subject: str,
    template_name: str,
    context: dict[str, Any],
    recipient_list: list[str],
    from_email: str | None = None,
    fail_silently: bool = False,
) -> int:
```

**Parameters:**

- `subject`: Email subject line
- `template_name`: Base template name without extension (e.g., "organisation_invite")
- `context`: Dictionary of variables for template rendering
- `recipient_list`: List of recipient email addresses
- `from_email`: Optional sender email (defaults to `DEFAULT_FROM_EMAIL`)
- `fail_silently`: If False, raises exceptions on errors

**Returns:**

- Number of successfully delivered messages (0 or 1)

**Raises:**

- `Exception`: If `fail_silently=False` and sending fails

## Troubleshooting

### MJML compilation fails

```bash
# Check for syntax errors in your MJML
docker compose exec node npx gulp mjml

# Validate MJML syntax
docker compose exec node npx mjml --validate path/to/template.mjml
```

### Django template tags not working

- Ensure `{% load i18n %}` is not in your MJML (it's added automatically)
- Check that Django template syntax is correct
- Verify context variables are passed correctly

### Emails not rendering properly

- Test in Mailpit: `http://localhost:8025`
- Check both HTML and text versions
- Verify MJML components are used correctly
- Review compiled HTML output in `ams/templates/emails/`

### Compiled templates not updating

```bash
# Manually recompile all templates
docker compose exec node npx gulp mjml

# Restart node container
docker compose restart node
```

## Migrating Existing Email Templates

To convert an existing HTML email template to MJML:

1. Identify the layout structure (header, content, footer)
2. Create a new `.mjml` file
3. Replace HTML tables with MJML components:
   - `<table>` → `<mj-section>` and `<mj-column>`
   - `<a>` buttons → `<mj-button>`
   - Inline styles → MJML attributes
4. Preserve Django template tags as-is
5. Compile and test
6. (Optional) Create corresponding `.txt` template if auto-generation isn't suitable
7. Update code to use `send_templated_email()`

Example conversion:

**Before (HTML):**

```html
<table style="width: 100%; background-color: #ffffff;">
  <tr>
    <td style="padding: 20px;">
      <a href="{{ url }}" style="background: #0056b3; color: white; padding: 10px 20px;">
        Click Here
      </a>
    </td>
  </tr>
</table>
```

**After (MJML):**

```xml
<mj-section background-color="#ffffff" padding="20px">
  <mj-column>
    <mj-button background-color="#0056b3" href="{{ url }}">
      Click Here
    </mj-button>
  </mj-column>
</mj-section>
```
