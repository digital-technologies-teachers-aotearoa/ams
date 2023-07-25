# AMS

## Frontend setup

## Basic static HTML & CSS. Using SASS as a CSS preprocessor.

## For a quick set up:

- Use Visual Studio Code as your code editor
- Install 'Live Sass Compiler' extension
- Open 'styles.scss' and hit 'Watch Sass' (at bottom of VS Code window)
- 'Sass' extension is not required, but is useful

    "liveSassCompile.settings.autoprefix": [
    
    ],
    "liveSassCompile.settings.excludeList": [
        "/**/node_modules/**",
        "/.vscode/**"
    ],
    "liveSassCompile.settings.includeItems": [
        "/scss/main.scss"
    ],
    "liveSassCompile.settings.generateMap": false,
    "liveSassCompile.settings.formats": [
        {
            "format": "expanded",
            "extensionName": ".css",
            "savePath": "/css",
            "savePathReplacementPairs": null
        },
        {
            "format": "compressed",
            "extensionName": ".min.css",
            "savePath": "/css",
        }
    ]