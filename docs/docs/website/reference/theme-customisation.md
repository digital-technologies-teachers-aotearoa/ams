# Theme customisation

**Who this page is for:** client website admins — the volunteers who run the day-to-day site once it's launched.

Customise your website's colours and appearance directly from the Wagtail admin interface—no code changes or technical knowledge required.

See [Tutorial 2: Branding & theme](../setup/branding-theme.md) for a step-by-step walkthrough of uploading your logo and setting your primary colour and font — this page covers every field in full.

## Quick start

1. Log into the Wagtail admin at `/cms/`
2. Navigate to **Settings** in the left sidebar
3. Select **Theme Settings**
4. Adjust colours using the colour picker fields
5. Click **Save** to apply changes instantly across your entire site

## What you can customise

The theme system allows you to customise colours for:

- **Brand colours**: Primary, secondary, success, info, warning, danger, light, and dark theme colours
- **Body colours**: Background and text colours for your pages
- **Link colours**: Link and hover colours
- **Navbar and footer colours**: Background colours
- **Typography**: Font families, sizes, weights, and line heights
- **Custom CSS**: Advanced overrides (use with caution)

All changes apply **instantly** across the entire website without requiring a server restart or code deployment.

## Understanding colour sections

The theme settings are organised into logical groups:

### Body colours

Control the base appearance of your pages:

- **Body text colour**: The default colour for all text
- **Body background**: The background colour of pages

### Theme colours

Define your brand identity:

- **Primary**: Your main brand colour (used for links, buttons, focus states)
- **Success**: For positive actions (green by default)
- **Info**: For informational content (blue by default)
- **Warning**: For cautionary content (yellow by default)
- **Danger**: For errors and dangerous actions (red by default)

Each theme colour includes subtle background, border, and text emphasis variants.

### Link colours

Customise how hyperlinks appear:

- **Link colour**: Default link colour
- **Link hover colour**: Colour when hovering over links

### Fonts

Configure typography settings:

- **Sans-serif font stack**: Font family for most text
- **Monospace font stack**: Font family for code
- **Body font family**: Which font stack to use for body text
- **Body font size**: Base font size (default: 1rem)
- **Body font weight**: Font weight (default: 400)
- **Body line height**: Spacing between lines (default: 1.5)

## Best practices

### Accessibility and contrast

**Always ensure sufficient contrast between text and backgrounds:**

- Minimum contrast ratio: 4.5:1 (WCAG AA standard)
- Preferred contrast ratio: 7:1 (WCAG AAA standard)
- Use online contrast checkers to verify your colour combinations
- Consider users with colour blindness when selecting colours

### Colour selection tips

- **Brand consistency**: Use your organisation's official brand colours for primary/secondary
- **Semantic colours**: Keep success=green, danger=red, warning=yellow for user familiarity
- **Start small**: Change one colour at a time to see its impact
- **Save frequently**: Changes can be reverted through the revision history

### Testing your changes

After saving theme changes:

1. Open your website in a new browser tab
2. Navigate to different page types (home, blog posts, forms, etc.)
3. Check on different devices (desktop, tablet, mobile)
4. Verify links, buttons, and alerts look correct

## Multi-site configuration

If your AMS installation manages multiple websites:

- Each site has its own independent theme settings
- Use the site switcher in the Wagtail admin to configure different sites
- Changes to one site don't affect others

## Advanced: Custom CSS

!!! warning "Use with Caution"
    Custom CSS can override all theme settings and potentially break your site's design. Only use this feature if you understand CSS.

The Custom CSS field allows you to add arbitrary CSS code that will be applied to all pages. This is useful for:

- Fine-tuning specific elements not covered by colour settings
- Adding custom animations or transitions
- Overriding specific Bootstrap components

Changes apply immediately but can cause unexpected behaviour if not tested thoroughly.

## Save and reuse your theme

Every field on this page — every colour, every dropdown (colour mode, sign in/sign up button style, separator type and width), the separator image, and the Custom CSS and Custom HTML boxes — can be saved to a file on your computer and loaded back in later.
This is useful for keeping a backup before you experiment, and for copying a finished theme from your [staging/UAT](../../getting-started/glossary.md#uat) site to your [production](../../getting-started/glossary.md#production) site.

### Export your theme

1. Open **Theme Settings** (see Quick Start above).
2. Click **Export Settings**, next to the **Save** button at the bottom of the page.
3. Your browser downloads a file named `theme-settings-<today's date>.json`.
   Keep it somewhere you'll find again, such as alongside your organisation's other records.

### Import a theme

1. Open **Theme Settings** on the site you want to update.
2. Click **Import Settings**, next to the **Export Settings** button.
3. Choose a file you exported earlier.
4. Confirm the warning that this will overwrite your current settings.
5. Wait for the "Successfully imported…" message, then check that the colour and font fields have updated.
6. Click **Save** to apply the imported theme.
   Importing only fills in the fields on the page — it doesn't save them for you.

### Copying a theme between sites

If your provider has set you up with a [staging/UAT](../../getting-started/glossary.md#uat) site as well as a production site, exporting from one and importing into the other is the easiest way to copy a finished theme across: build and check it on UAT, export, then import into production once you're happy with it.

## Troubleshooting

### Changes not appearing

1. **Hard refresh your browser**: Press Ctrl+F5 (Windows/Linux) or Cmd+Shift+R (Mac)
2. **Verify you saved**: Check for the "Theme Settings updated" success message
3. **Check the correct site**: Ensure you're viewing the site you edited
4. **Try incognito mode**: Opens a fresh browser session without cached data

### Invalid colour error

Colours must be in hexadecimal format:

- ✅ Valid: `#ffffff`, `#fff`, `#0d6efd`
- ❌ Invalid: `white`, `rgb(255,255,255)`, `#gggggg`
- Always include the `#` symbol
- Use only valid hex characters: 0-9 and A-F

### Need to undo changes?

Theme settings are automatically saved with revision history, however a website administrator or developer is required to restore a previous version.
See [Save and reuse your theme](#save-and-reuse-your-theme) below for a way to get back to a known-good state yourself, without developer involvement — as long as you exported a copy first.

## Getting help

If you need assistance:

- Contact your site administrator
- Review Bootstrap 5.3 colour documentation for design inspiration
