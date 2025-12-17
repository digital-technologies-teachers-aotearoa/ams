# Theme Customization

The AMS platform provides a powerful theme customization system that allows Wagtail administrators to customize the website's appearance without requiring code changes or deployments.

## Overview

The theme system allows customization of Bootstrap 5.3 CSS variables including:

- **Theme colors**: Primary, secondary, success, info, warning, danger, light, dark
- **Body colors**: Background and text colors for both light and dark modes
- **Link colors**: Link and hover colors for both light and dark modes
- **Border colors**: Default border colors for both light and dark modes

All changes apply instantly across the entire website without requiring a server restart or code deployment.

## Accessing Theme Settings

1. Log into the Wagtail admin at `/cms/`
2. Navigate to **Settings** in the left sidebar
3. Select **Theme Settings**
4. Adjust colors using the color picker fields
5. Click **Save** to apply changes site-wide

## Features

### Color Customization

Each color can be customized with a simple color picker interface:

- **Theme Colors**: Define your brand colors that are used throughout the site
- **Light/Dark Mode Support**: Separate color values for light and dark modes ensure optimal readability
- **Validation**: All color values are validated to ensure they are proper hex color codes (`#rrggbb`)

### Performance

The theme system is designed for zero performance impact:

- **Caching**: Generated CSS is cached indefinitely in memory
- **Cache Invalidation**: Automatic invalidation when settings change
- **Single Query**: Settings loaded once per request via Wagtail's built-in caching
- **CSS Injection**: Theme CSS injected inline in the HTML head for immediate application

### Dark Mode Support

Bootstrap 5.3's dark mode is fully supported with separate color values:

- Colors automatically switch based on `[data-bs-theme="dark"]` attribute
- Separate fields for light and dark mode variants of colors that differ
- Theme colors (primary, secondary, etc.) work automatically in both modes

## Technical Details

### How It Works

1. **Model**: `ThemeSettings` stores color values in the database
2. **Template Tag**: `{% theme_css_variables %}` generates CSS custom properties
3. **Caching**: Generated CSS is cached with a version key for invalidation
4. **Bootstrap Integration**: CSS variables override Bootstrap's defaults

### CSS Variables Generated

The system generates CSS custom properties in two scopes:

```css
:root,
[data-bs-theme="light"] {
  --bs-primary: #0d6efd;
  --bs-body-bg: #ffffff;
  --bs-body-color: #212529;
  --bs-link-color: #0d6efd;
  /* ... and more */
}

[data-bs-theme="dark"] {
  --bs-body-bg: #212529;
  --bs-body-color: #dee2e6;
  --bs-link-color: #6ea8fe;
  /* ... and more */
}
```

### Cache Strategy

- **Cache Key**: `theme_css_v{version}_site{site_id}`
- **Version Tracking**: `css_version` field auto-increments on save
- **Invalidation**: Old cache automatically cleared on save
- **TTL**: Infinite (manual invalidation only)

## Default Colors

The system ships with Bootstrap 5.3's default color palette:

| Color | Light Mode | Dark Mode (if different) |
|-------|------------|--------------------------|
| Primary | `#0d6efd` | - |
| Secondary | `#6c757d` | - |
| Success | `#198754` | - |
| Info | `#0dcaf0` | - |
| Warning | `#ffc107` | - |
| Danger | `#dc3545` | - |
| Body Background | `#ffffff` | `#212529` |
| Body Text | `#212529` | `#dee2e6` |
| Link | `#0d6efd` | `#6ea8fe` |
| Link Hover | `#0a58ca` | `#8bb9fe` |
| Border | `#dee2e6` | `#495057` |

## Best Practices

### Color Selection

- **Contrast**: Ensure sufficient contrast between text and background colors (WCAG AA: 4.5:1 minimum)
- **Consistency**: Use your brand colors consistently across primary/secondary themes
- **Testing**: Test both light and dark modes after making changes
- **Accessibility**: Consider color blindness when selecting warning/danger colors

### Performance Considerations

- Changes are cached automatically - no performance impact after first page load
- CSS is inlined in the HTML head (< 2KB typical)
- No external requests or file I/O on page render
- Cache cleared automatically when settings change

### Multi-site Considerations

Each Wagtail site can have its own theme settings:

- Settings are per-site, not global
- Use the site switcher in admin to configure different sites
- Each site maintains its own cache

## Troubleshooting

### Changes Not Appearing

1. Clear your browser cache (Ctrl+F5 / Cmd+Shift+R)
2. Check that you saved the settings in admin
3. Verify you're viewing the correct site
4. Check browser console for CSS errors

### Invalid Color Error

- Colors must be in hex format: `#rrggbb` or `#rgb`
- Include the `#` symbol
- Use valid hex characters (0-9, A-F)

### Performance Issues

If you experience performance issues:

1. Check your cache backend configuration in settings
2. Consider upgrading to Redis for production (currently using locmem)
3. Monitor cache hit rates
