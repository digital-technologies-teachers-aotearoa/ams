# Email Templates

This project uses MJML for creating responsive, email-client-compatible HTML emails.
This document describes how the AMS project uses MJML for email templates, including the shared component system, build pipeline, and best practices.

## Overview

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

### Benefits

- **Responsive by default**: MJML automatically generates responsive HTML emails
- **Consistent styling**: Shared includes ensure all emails follow the same design system
- **Developer-friendly**: Cleaner syntax than raw HTML email markup
- **Django integration**: Templates support Django template tags for dynamic content

## Build Pipeline

### How It Works

1. **Source files**: Email templates are written as `.mjml` files in various app directories
2. **Compilation**: The Gulp build process compiles `.mjml` files to `.html` files
3. **In-place output**: HTML files are generated in the same directory as their source `.mjml` files
4. **Django integration**: Compiled HTML files are loaded by Django's email system
5. **Git ignored**: Compiled `.html` files are ignored by Git (only `.mjml` source files are tracked)

### Build Commands

Compile all MJML templates:

```bash
docker compose exec node npx gulp mjml
```

Watch for changes (auto-compile):

```bash
docker compose exec node npx gulp dev
```

Build all assets including MJML:

```bash
docker compose exec node npx gulp build
```

### Files Excluded from Compilation

Any MJML file starting with an underscore (`_*.mjml`) is excluded from compilation. These are include files used by other templates.

## Using Shared Includes

### Head Attributes

Include shared MJML attributes in your email template's `<mj-head>` section:

```xml
<mjml>
  <mj-head>
    <mj-title>{% trans "Your Email Title" %}</mj-title>
    <mj-preview>{% trans "Preview text here" %}</mj-preview>
    <mj-attributes>
      <mj-include path="../../_email_includes/_head_attributes.mjml" />
    </mj-attributes>
  </mj-head>
  <mj-body background-color="#f8f9fa">
    <!-- Your email content -->
  </mj-body>
</mjml>
```

### Head Styles (Optional)

If you need the shared CSS styles:

```xml
<mj-head>
  <!-- ... -->
  <mj-style inline="inline">
    <mj-include path="../../_email_includes/_head_styles.mjml" />
  </mj-style>
</mj-head>
```

### Standard Footer

For simple emails with a generic footer message:

```xml
<mj-body background-color="#f8f9fa">
  <!-- Your email content -->

  <!-- Footer -->
  <mj-include path="../../_email_includes/_footer.mjml" />
</mj-body>
```

**Custom Footers**: Many templates use custom footers with specific messaging (e.g., "You're receiving this because you are a staff member") or include action URLs. In these cases, don't use the shared footer—write a custom one instead.

### Staff Footer

For staff notification emails:

```xml
<mj-body background-color="#f8f9fa">
  <!-- Your email content -->

  <!-- Footer -->
  <mj-include path="../../_email_includes/_staff_footer.mjml" />
</mj-body>
```

This footer includes a message indicating the recipient is receiving the email because they are a staff member.

## Using mj-class for Consistent Styling

The shared `_head_attributes.mjml` file includes `_head_styles.mjml`, which defines reusable `mj-class` declarations. Using these classes ensures consistent styling across all email templates and reduces code verbosity.

### Example: Using mj-class

**Before (inline styles):**

```xml
<mj-section background-color="#0056b3" padding="30px 20px">
  <mj-column>
    <!-- prettier-ignore -->
    <mj-text font-size="28px" font-weight="bold" color="#ffffff" align="center">
      {% trans "Email Title" %}
    </mj-text>
  </mj-column>
</mj-section>
```

**After (using mj-class):**

```xml
<mj-section mj-class="section-header-primary">
  <mj-column>
    <!-- prettier-ignore -->
    <mj-text mj-class="header-primary">
      {% trans "Email Title" %}
    </mj-text>
  </mj-column>
</mj-section>
```

### When NOT to Use mj-class

Some styles cannot use `mj-class` and must remain inline:

1. **Table cell styles**: `<td style="...">` elements cannot use `mj-class`
2. **Link styles**: Styles on `<a>` tags within `<mj-text>` must be inline
3. **One-off custom styles**: Unique styles that don't fit a reusable pattern

**Example (table styles must stay inline):**

```xml
<mj-table>
  <tr>
    <!-- prettier-ignore -->
    <td style="padding: 8px 0; font-weight: bold; width: 40%">
      {% trans "Label:" %}
    </td>
    <td style="padding: 8px 0">{{ value }}</td>
  </tr>
</mj-table>
```

## Django Template Integration

### Template Tags

MJML templates support Django template tags:

```xml
<!-- prettier-ignore -->
<mj-text>
  {% load i18n %}
  {% trans "Translatable text" %}
</mj-text>

<!-- prettier-ignore -->
<mj-text>
  {% blocktrans with name=user.name %}
  Hello {{ name }}!
  {% endblocktrans %}
</mj-text>
```

### Variables

Use Django template variables:

```xml
<mj-text>{{ user.email }}</mj-text>
<mj-button href="{{ action_url }}">Click Here</mj-button>
```

### Conditional Content

Use Django conditionals:

```xml
<!-- prettier-ignore -->
{% if show_warning %}
<mj-section background-color="#fff3cd" border-left="4px solid #ffc107" padding="15px">
  <mj-column>
    <mj-text>{% trans "Warning message" %}</mj-text>
  </mj-column>
</mj-section>
{% endif %}
```

**Important**: For conditionals around MJML tags, use `<mj-raw>`:

```xml
<mj-raw>{% if condition %}</mj-raw>
<mj-section>
  <!-- content -->
</mj-section>
<mj-raw>{% endif %}</mj-raw>
```

## Creating a New Email Template

### Step 1: Choose Location

Place your template in the appropriate app directory.

### Step 2: Create MJML File

Create a `.mjml` file with this basic structure:

```xml
<mjml>
  <mj-head>
    <mj-title>{{ subject }}</mj-title>
    <mj-preview>{{ preview_text }}</mj-preview>
    <mj-attributes>
      <mj-include path="../../_email_includes/_head_attributes.mjml" />
    </mj-attributes>
  </mj-head>
  <mj-body background-color="#f8f9fa">
    <!-- Header -->
    <mj-section mj-class="section-header-primary">
      <mj-column>
        <mj-text mj-class="header-primary">
          {% trans "Email Title" %}
        </mj-text>
      </mj-column>
    </mj-section>

    <!-- Content -->
    <mj-section mj-class="section-content">
      <mj-column>
        <mj-text mj-class="text-body">
          {% trans "Your email content here" %}
        </mj-text>
      </mj-column>
    </mj-section>

    <!-- Footer -->
    <mj-include path="../../_email_includes/_footer.mjml" />
  </mj-body>
</mjml>
```

**Remember**: Adjust the include paths based on your template's location.

### Step 3: Compile

Compile the MJML to HTML (if it hasn't occurred automatically):

```bash
docker compose exec node npx gulp mjml
```

### Step 4: Update .gitignore (if needed)

If you created a template in a new directory, add the compiled HTML pattern to `.gitignore`:

```text
# Compiled MJML email templates
ams/templates/new_app/emails/*.html
```

### Step 5: Send Email in Django

Use the HTML template in your Django email code when calling `send_templated_email()` from `ams.utils.email`.

## Best Practices

### 1. Use Shared Includes

Always use the shared `_head_attributes.mjml` include for consistent styling across all emails.

### 2. Follow the Color Palette

Use the defined color palette to maintain visual consistency.

### 3. Make Text Translatable

Wrap all user-facing text in `{% trans %}` or `{% blocktrans %}` tags.

### 4. Test in Multiple Email Clients

MJML handles most cross-client compatibility, but always test major emails in:

- Gmail
- Outlook
- Apple Mail
- Mobile clients

### 5. Keep Content Focused

- Use clear, concise subject lines
- Put the most important information first
- Use headers and sections to organize content
- Include clear calls-to-action with buttons

### 6. Custom Footers When Needed

Don't force-fit the generic footer if your email needs specific footer content (like URLs, specific disclaimers, or context-specific messages).

### 7. Preview Text

Always include a `<mj-preview>` tag with a meaningful preview (shown in email client previews).

## Troubleshooting

### Template Not Compiling

**Problem**: MJML file isn't generating HTML output

**Solutions**:

1. Check that the file doesn't start with `_` (reserved for includes)
2. Verify the Gulp build process is running
3. Check the terminal for MJML compilation errors
4. Validate your MJML syntax at [MJML Playground](https://mjml.io/try-it-live)

### Include Path Errors

**Problem**: "File not found" errors for includes

**Solutions**:

1. Check the relative path based on your template's location
2. Remember: `../../_email_includes/` for nested dirs, `../_email_includes/` for top-level
3. Ensure `_email_includes/` directory exists

### Styles Not Applying

**Problem**: Email doesn't look right

**Solutions**:

1. Ensure you're including `_head_attributes.mjml`
2. Check that the HTML file was regenerated after MJML changes
3. Clear email client cache (some clients cache heavily)

### Django Tags Not Rendering

**Problem**: `{% trans %}` tags showing as literal text

**Solutions**:

1. Ensure you're loading the compiled `.html` file, not the `.mjml` file
2. Check that `{% load i18n %}` is present at the top of your template
3. Verify the Gulp `prependDjangoTags()` function is working (should add `{% load i18n %}` to compiled HTML)

## Resources

- [MJML Documentation](https://documentation.mjml.io/)
- [MJML Try It Live](https://mjml.io/try-it-live) - Test MJML code in real-time
- [MJML Component Reference](https://documentation.mjml.io/#components)
