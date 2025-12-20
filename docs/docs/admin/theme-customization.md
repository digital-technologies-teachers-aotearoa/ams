# Theme Customization

Customize your website's colors and appearance directly from the Wagtail admin interface—no code changes or technical knowledge required.

## Quick Start

1. Log into the Wagtail admin at `/cms/`
2. Navigate to **Settings** in the left sidebar
3. Select **Theme Settings**
4. Adjust colors using the color picker fields
5. Click **Save** to apply changes instantly across your entire site

## What You Can Customize

The theme system allows you to customize colors for:

- **Brand Colors**: Primary, secondary, success, info, warning, danger, light, and dark theme colors
- **Body Colors**: Background and text colors for your pages
- **Link Colors**: Link and hover colors
- **Component Colors**: Borders, buttons, alerts, and other UI elements
- **Typography**: Font families, sizes, weights, and line heights
- **Custom CSS**: Advanced overrides (use with caution)

All changes apply **instantly** across the entire website without requiring a server restart or code deployment.

## Understanding Color Sections

The theme settings are organized into logical groups:

### Body Colors

Control the base appearance of your pages:

- **Body text color**: The default color for all text
- **Body background**: The background color of pages

### Theme Colors

Define your brand identity:

- **Primary**: Your main brand color (used for links, buttons, focus states)
- **Success**: For positive actions (green by default)
- **Info**: For informational content (blue by default)
- **Warning**: For cautionary content (yellow by default)
- **Danger**: For errors and dangerous actions (red by default)

Each theme color includes subtle background, border, and text emphasis variants.

### Link Colors

Customize how hyperlinks appear:

- **Link color**: Default link color
- **Link hover color**: Color when hovering over links

### Fonts

Configure typography settings:

- **Sans-serif font stack**: Font family for most text
- **Monospace font stack**: Font family for code
- **Body font family**: Which font stack to use for body text
- **Body font size**: Base font size (default: 1rem)
- **Body font weight**: Font weight (default: 400)
- **Body line height**: Spacing between lines (default: 1.5)

## Best Practices

### Accessibility and Contrast

**Always ensure sufficient contrast between text and backgrounds:**

- Minimum contrast ratio: 4.5:1 (WCAG AA standard)
- Preferred contrast ratio: 7:1 (WCAG AAA standard)
- Use online contrast checkers to verify your color combinations
- Consider users with color blindness when selecting colors

### Color Selection Tips

- **Brand Consistency**: Use your organization's official brand colors for primary/secondary
- **Semantic Colors**: Keep success=green, danger=red, warning=yellow for user familiarity
- **Start Small**: Change one color at a time to see its impact
- **Save Frequently**: Changes can be reverted through the revision history

### Testing Your Changes

After saving theme changes:

1. Open your website in a new browser tab
2. Navigate to different page types (home, blog posts, forms, etc.)
3. Check on different devices (desktop, tablet, mobile)
4. Verify links, buttons, and alerts look correct

## Multi-site Configuration

If your AMS installation manages multiple websites:

- Each site has its own independent theme settings
- Use the site switcher in the Wagtail admin to configure different sites
- Changes to one site don't affect others

## Advanced: Custom CSS

!!! warning "Use with Caution"
    Custom CSS can override all theme settings and potentially break your site's design. Only use this feature if you understand CSS.

The Custom CSS field allows you to add arbitrary CSS code that will be applied to all pages. This is useful for:

- Fine-tuning specific elements not covered by color settings
- Adding custom animations or transitions
- Overriding specific Bootstrap components

Changes apply immediately but can cause unexpected behavior if not tested thoroughly.

## Troubleshooting

### Changes Not Appearing

1. **Hard refresh your browser**: Press Ctrl+F5 (Windows/Linux) or Cmd+Shift+R (Mac)
2. **Verify you saved**: Check for the "Theme Settings updated" success message
3. **Check the correct site**: Ensure you're viewing the site you edited
4. **Try incognito mode**: Opens a fresh browser session without cached data

### Invalid Color Error

Colors must be in hexadecimal format:

- ✅ Valid: `#ffffff`, `#fff`, `#0d6efd`
- ❌ Invalid: `white`, `rgb(255,255,255)`, `#gggggg`
- Always include the `#` symbol
- Use only valid hex characters: 0-9 and A-F

### Need to Undo Changes?

Theme settings are automatically saved with revision history, however a website administrator or developer is required to restore a previous version.
You can also export settings as make changes, which is a great way to keep a backup in case a reset is needed.

## Getting Help

If you need assistance:

- Contact your site administrator
- Review Bootstrap 5.3 color documentation for design inspiration
