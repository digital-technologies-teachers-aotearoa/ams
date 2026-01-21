# MJML Email Templates

This directory contains MJML source templates that are compiled to HTML at build time.

## Quick Start

1. Create a new `.mjml` file in this directory
2. Use MJML components for layout
3. Use Django template tags for dynamic content
4. Compilation happens automatically (in dev) or during build (in production)
5. Compiled templates appear in `ams/templates/emails/`

## Template Structure

```xml
<mjml>
  <mj-head>
    <mj-title>{% trans "Email Subject" %}</mj-title>
    <mj-attributes>
      <mj-all font-family="Arial, sans-serif" />
    </mj-attributes>
  </mj-head>
  <mj-body background-color="#f8f9fa">
    <!-- Your email content here -->
    <mj-section>
      <mj-column>
        <mj-text>Hello {{ user.name }}!</mj-text>
        <mj-button href="{{ url }}">Click Here</mj-button>
      </mj-column>
    </mj-section>
  </mj-body>
</mjml>
```

## Important Notes

- **Don't include** `{% load i18n %}` - it's added automatically during compilation
- **Use Django tags freely** - they are preserved in the compiled output
- **Plaintext is auto-generated** - No need to create `.txt` templates (they're auto-generated from HTML using html2text)
- **Custom .txt optional** - Only create `.txt` templates when you need precise control over plaintext formatting
- **Prefix with underscore** `_base.mjml` for reusable templates that shouldn't be compiled directly

## Common MJML Components

- `<mj-section>` - Horizontal container
- `<mj-column>` - Vertical container (must be inside section)
- `<mj-text>` - Text content
- `<mj-button>` - Call-to-action button
- `<mj-image>` - Responsive images
- `<mj-divider>` - Horizontal line
- `<mj-spacer>` - Vertical spacing
- `<mj-table>` - HTML table (for data, not layout)

## Testing Changes

```bash
# Manually compile (dev container auto-compiles on save)
docker compose exec node npx gulp mjml

# View emails in Mailpit
open http://localhost:8025
```

## Resources

- [Full Documentation](../../docs/docs/developer/email-templates.md)
- [MJML Documentation](https://documentation.mjml.io/)
- [MJML Try it Live](https://mjml.io/try-it-live)
