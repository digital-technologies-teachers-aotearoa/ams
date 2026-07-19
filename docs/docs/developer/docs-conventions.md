# Documentation conventions

**Who this page is for:** developers and the operator writing or updating AMS documentation.

This page is binding: it records the structural decisions made for the [client onboarding & website setup documentation effort](https://github.com/digital-technologies-teachers-aotearoa/ams) (see `docs/onboarding-documentation-scope.md` and `docs/onboarding-documentation-tasks.md` in the repo root for the full plan).
Later documentation tasks follow these conventions rather than re-deciding them.

## Where each doc type lives

| Nav section                 | Directory                    | Audience                | What goes here                                                                                                                                                       |
| --------------------------- | ---------------------------- | ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Home                        | `docs/docs/index.md`         | Everyone                | What AMS is                                                                                                                                                          |
| Features                    | `docs/docs/features.md`      | Everyone                | Product capability overview                                                                                                                                          |
| Getting started             | `docs/docs/getting-started/` | Client decision-makers  | Onboarding overview, decision questionnaire, costs sheet, accounts & access checklist, working-with-designers one-pager, and the two glossaries (settings and terms) |
| Building your website       | `docs/docs/tutorials/`       | Client website admins   | The empty-site-to-launch tutorial series                                                                                                                             |
| Website administrator guide | `docs/docs/admin/`           | Client website admins   | Standing reference (not a guided path) for CMS, events, resources, forum, billing, theme customization                                                               |
| Provider guide              | `docs/docs/provider/`        | Provider                | Provisioning runbook, client-communication templates                                                                                                                 |
| Developer documentation     | `docs/docs/developer/`       | Developer / contributor | Codebase contribution, architecture, platform-agnostic deployment                                                                                                    |

**Decision — Provider guide is top-level, not under Developer documentation.**
The operator runbook's audience is "person running a client's instance," which has more in common with the Getting started/Building your website audiences (a concrete client, a concrete handoff) than with "person contributing to the AMS codebase."
Keeping it top-level also means it doesn't get lost under codebase-contribution content a client-facing reader would never open.
The repo stays public and the runbook contains no secrets, so there's no publishing reason to nest it.

**Decision — both glossaries live under Getting started**, not in a separate top-level "Reference" section: `docs/docs/getting-started/settings-glossary.md` (T03) and `docs/docs/getting-started/glossary.md` (T04).
Both are primarily consulted during onboarding and by non-technical readers, and adding a fourth top-level section for two pages isn't worth the nav complexity.
Other pages link to them with `getting-started/glossary.md#term` anchors.

**Decision — each new top-level section gets its own `index.md` landing page**, distinct from its content pages, following the existing pattern in `admin/index.md`.
The landing page states what the section is, who it's for, and links to its pages.
`getting-started/index.md` in particular becomes the onboarding overview & timeline page (T05) — the "front door" of the intake pack — rather than a separate landing plus a separate overview page.

## "Who this page is for" header

Every page in Getting started, Building your website, the Website administrator guide, the Provider guide, and the working-with-designers one-pager starts with:

```markdown
**Who this page is for:** <audience>, <one clause of calibration if useful>.
```

Use the audience names from scope §3 verbatim (client decision-makers, client website admins, operator, third-party designers/agencies) so a reader skimming multiple pages recognises the same audience language.
Developer docs may omit this header (audience is implicit: developers) unless the page also serves the operator.

## Markdown source formatting

- **One sentence per line:** write prose as one sentence per source line (semantic linefeeds), not wrapped to a fixed column width.
  This keeps diffs scoped to the sentence that actually changed, instead of reflowing an entire paragraph.
  Markdown joins consecutive lines within a paragraph into one flowing line when rendered, so this is a source-only convention — it does not change how a page displays.
  Applies to prose paragraphs and list-item text across all documentation pages, including client-facing, provider, and developer pages; tables and code blocks are exempt (there's no useful "sentence" to split them by).
  A list item with more than one sentence continues on the next line, indented to align under the item's text, rather than starting a new list item.

## Style rules for client-facing pages

Client-facing pages (Getting started, Building your website, Website administrator guide) are written for the audiences in scope §3 — assume no technical knowledge and possibly a tablet, not a desktop with two monitors.

- **Reading level:** aim for [Flesch–Kincaid grade 8](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests) or lower.
  Short sentences, common words, no unexplained acronyms.
- **Numbered steps:** any procedure is a numbered list, not prose paragraphs.
- **One action per step:** each numbered step is a single click, field entry, or decision — never "do X, then Y, then check Z."
- **Screenshot per step:** each step in a tutorial (Building your website series) carries one screenshot showing the result of that step.
  Reference pages (Website administrator guide) use screenshots more sparingly, where they resolve ambiguity rather than illustrating every click.
- **Glossary linking:** the first use of a jargon term on a page links to its entry in `getting-started/glossary.md#term` (e.g. `[DNS](../getting-started/glossary.md#dns)`).
  Don't re-explain the term inline — link instead.

Provider guide pages use the opposite register deliberately: terse, technical, no glossary links, no reading-level target — the operator is technical (scope §3).

## Screenshot conventions

1. **Directory layout:** `docs/docs/images/<section>/`, mirroring the nav section directory names above, e.g. `docs/docs/images/tutorials/`, `docs/docs/images/getting-started/`, `docs/docs/images/admin/`.
2. **File naming:** `<page-slug>-<step-number>-<short-description>.png`, all lowercase, words separated by hyphens.
   Example: `branding-theme-03-colour-picker.png` for step 3 of the branding & theme tutorial.
3. **Fixed viewport:** 1280×800px for every screenshot, regardless of the audience reading the docs on a tablet — the Wagtail/Django admin UI itself is desktop-oriented, and a fixed viewport is what makes screenshots byte-stable across regenerations (required by T02).
4. **Demo organisation:** all screenshots and examples use a fictional association **"Mathematics Teachers Association"**.
   This name is **not** what `sample_data` currently produces — `setup_cms`/`sample_data` set `AssociationSettings.association_short_name`/`association_long_name` to `"{Language} AMS"` (e.g. "English AMS"), not a fixed org name.
   **This is a requirement on T02**: the screenshot suite's setup step must update `AssociationSettings` for the seeded site(s) to "Mathematics Teachers Association" after running `sample_data`, so screenshots show a stable, deliberately-chosen name rather than the language-derived placeholder.
   Do not rename the organisation in `sample_data` itself as part of that work unless the developer docs audit (T24) decides sample data should default to it too — that's a separate decision.
5. **Playwright-regenerable rule:** no screenshot may be committed unless the Playwright suite can regenerate it byte-for-visually-identical.
   If a page needs a screenshot before T02 exists (or before that screen is added to the manifest), leave a placeholder comment instead: `<!-- TODO screenshot: <description of what the image should show> -->` and note the gap in that task's completion notes.
6. **Annotated-image exception:** rare.
   Only when a callout (arrow, box, highlight) is necessary to point at a specific UI element that a caption alone can't clarify.
   An annotated image:
   - is still generated by first letting the Playwright suite capture the unannotated base screenshot (so the underlying UI stays regenerable), then adding the annotation as a manual, documented step;
   - is named with an `-annotated` suffix, e.g. `branding-theme-03-colour-picker-annotated.png`;
   - is recorded in the T02 manifest with a note of which base image it annotates and what tool/steps produced the annotation, so a future contributor can redo it after a UI change;
   - prefer a plain caption over an annotation whenever the caption alone resolves the ambiguity.

## Definition of done for feature PRs that change documented UI

A PR that changes UI covered by these docs is not done until:

1. The Playwright screenshot suite has been re-run and any changed screenshots are included in the PR;
2. Any page whose steps, labels, or field names changed is updated to match;
3. The manifest still has no orphaned or stale entries for the changed screens.

## How to regenerate screenshots

The screenshot suite lives in `docs/screenshots/`.
It captures against Chromium only, since a single deterministic renderer is what matters for byte-stable images, not cross-browser coverage.

**Prerequisites:**

1. From the repo root, run `./docs/screenshots/seed.sh` (or `just docs-seed`).
   This flushes the database and rebuilds a clean skeleton site — `setup_cms` (sites, home pages, locales) plus an admin account — deliberately **not** `sample_data`, since screenshots should show what a real new client's site looks like (empty), not `sample_data`'s fixture events, resources, and articles.
   It also sets every site's `AssociationSettings` to the fixed demo name (`setup_cms` on its own sets a language-derived placeholder like "English AMS" instead) and starts the Django dev server in the background, waiting until it responds before exiting.
   `manage.py flush` truncates data but doesn't replay migrations, which deletes Wagtail's root page/collection (created by data migrations inside the `wagtail` package) without restoring them — `seed.sh` runs `manage.py ensure_wagtail_root` straight after flushing to recreate them, otherwise `setup_cms` fails silently with "Root page not found."
   Screenshot content reflects whichever languages `AMS_ENABLED_LANGUAGES` has enabled in your `.envs/.local/django.ini` (e.g. the CMS dashboard's page list differs between an `en`-only env and an `mi,en` env) — keep this env var stable across regenerations of the same image, or expect unrelated-looking diffs.

**Regenerate every screenshot in the manifest:**

```
docker-compose exec node npm run docs:screenshots
```

This overwrites every image listed in `docs/screenshots/manifest.json` deterministically — running it twice produces the same images (the suite hides `#djDebugRoot`, the Django Debug Toolbar's container, before every capture, since its live query/timing stats would otherwise change on every request and break determinism).

**Check for orphaned images** (in the manifest but not embedded in a doc page, or on disk but not in the manifest, or embedded in a doc page but missing from the manifest):

```
docker-compose exec node npm run docs:screenshots:check
```

**Adding a new screenshot:** add a capture step to the `steps` object in `docs/screenshots/run.mjs`, add an entry to `docs/screenshots/manifest.json` (file path per the naming convention above, the step name, and the doc page(s) that will embed it), embed the image in the doc page, then run the two commands above.

Two example screenshots below prove the pipeline end to end; they're captured by `run.mjs`'s `exampleLogin` and `exampleDashboard` steps.
Tutorial tasks (T13 onward) add their own steps for the screens they document, rather than reusing these.

![The AMS sign-in page](../images/developer/docs-conventions-01-example-login.png)

![The Wagtail CMS dashboard](../images/developer/docs-conventions-02-example-dashboard.png)
