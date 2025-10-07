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
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-exclamation-triangle-fill text-warning fs-2" viewBox="0 0 16 16">
  <path d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5m.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2" />
</svg>
```

## Notes

- You can add any icon SVG to the `icons/` template directory, not just Bootstrap Icons.
- The tag will append your classes to the existing SVG class attribute.
- Copying SVG files was chosen to ensure rendering icons was fast for users, rather than having the user download an icon font that has many unused icons.
