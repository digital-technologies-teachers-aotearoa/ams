# Stylesheet editing

Basic static HTML & CSS. Using SASS as a CSS preprocessor.

- Use Visual Studio Code as your code editor
- Open frontend/ folder as a workspace
- Install 'Live Sass Compiler' extension with this json config:

```
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
```

- Open 'main.scss' and hit 'Watch Sass' (at bottom of VS Code window)
- 'Sass' extension is not required, but is useful
