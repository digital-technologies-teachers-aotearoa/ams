# Icons

This project supports inline SVG Bootstrap Icons in Django templates using a custom template tag.

## How to use

1. **Add SVGs:**

   - Place your desired SVG icon files in `ams/templates/icons/` (e.g., `ams/templates/icons/exclamation-triangle-fill.svg`).
   - Use the original SVG markup from [https://icons.getbootstrap.com/](https://icons.getbootstrap.com/).

2. **Load the Tag in Your Template:**

   ```django
   {% load icon %}
   ```

3. **Render an Icon Inline:**

   ```django
   {% icon "exclamation-triangle-fill" "text-warning fs-2" %}
   ```

   - The first argument is the icon name (without `.svg`).
   - The second argument is optional and adds extra CSS classes to the `<svg>` tag.

### Example output

```html
<svg ... class="bi bi-exclamation-triangle-fill text-warning fs-2" ...>
  ...
</svg>
```

## Notes

- You can technically add any icon SVG to the `icons/` template directory.
- The tag will append your classes to the existing SVG class attribute.
- Copying SVG files was chosen to ensure rendering icons was fast for users, rather than having the user download an icon font that has many unused icons.
