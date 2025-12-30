# Icons Directory

This directory stores Bootstrap icons that are copied during the build process.

## Purpose

The `copyIcons` task in `gulpfile.mjs` copies SVG icons from the `bootstrap-icons` npm package into this directory during the build process. These icons are then available for use in Django templates.

## Contents

- `*.svg` - Bootstrap icon files (automatically generated, not tracked in git)
- `README.md` - This file

## Build Process

Icons are copied by running:
```bash
npm run build
```

Or specifically for icons:
```bash
gulp icons
```

## Why This Directory Exists in Git

This directory is tracked in git (with a `.gitignore` for `*.svg` files) to ensure:
1. The directory exists when code is checked out in CI/CD pipelines
2. The build process has proper permissions to write icon files
3. Developers understand the purpose of this directory
