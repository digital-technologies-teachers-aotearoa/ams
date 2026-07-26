# Working with designers & agencies

**Who this page is for:** third-party designers/agencies — an external design or branding agency a client has hired to help with their AMS website's look and content.

If you've been asked to design or brand a client's AMS website, read this one page before you start.
It explains what AMS can and can't do, so the designs you produce can actually be built — sending this page early avoids reworking finished designs later.

## AMS is a complete website, not a backend for your own frontend

AMS is a single, self-contained system: it runs the public pages, the membership area, billing, and the [forum](glossary.md#forum) together, as one website.
It is **not a headless system** — there is no supported way for a separately built frontend (a custom React site, a static site, or any other independent build) to read AMS's pages or membership data and display them through your own code.

In practice, this means you can't design and build your own site and hand it over expecting your client's provider to "plug it into" AMS as a backend.
The website your client's members and visitors use has to be built inside AMS itself, using the system described below — or, if your agency wants to host something entirely separate, see [If your agency wants to host its own site](#if-your-agency-wants-to-host-its-own-site).

## How your designs actually get built

Two separate layers make up an AMS website's appearance:

1. **Sitewide theme** — brand colours, fonts, and (optionally) custom CSS, set once for the whole site rather than chosen per page.
   See [theme customization](../website/reference/theme-customization.md) for what a non-developer can change, and [the theme system](../developer/theme-system.md) for the technical detail.
2. **Page content and structure** — built from a fixed set of content blocks in the [CMS](glossary.md#cms): headings, paragraphs, images, image grids and carousels, multi-column layouts, full-width banner sections, video embeds, and contact forms.
   Your client's provider, or a trained content editor, assembles these per page — there's no way to hand over a finished visual layout and have it reproduced exactly; it gets translated into the nearest combination of these blocks and the sitewide theme.

A few specific limits are worth knowing before you design, since they come up often:

- Text and heading colours and fonts are set once for the whole site — not chosen separately for each page or each heading.
- The heading block used for section headings within a page offers a size (heading levels 2 to 4) and left/centre alignment only — no per-heading colour or weight.
- Only the home page's main title (and optional subtitle) supports its own custom colour and font weight — this is a one-off component, not something available on every page or heading.
- A full-width banner section's background is either an uploaded image or the site's theme colour — not a freely chosen one-off colour for that section.
  Individual feature tiles inside such a section can each have their own background colour or image, if that level of detail matters to a design.
- A separate language-selection landing page isn't needed: each language's pages live at their own address (e.g. `/en/about`, `/mi/about`), AMS routes visitors to the right one automatically, and a switcher lets them change languages themselves.

Anything beyond these options — a genuinely custom layout, animation, or one-off visual treatment — needs a developer to build, and isn't something the client can change themselves after launch.

## What's useful to hand over

- Brand colours as hex or RGB values (e.g. `#1A73E8`), not just "by eye" from other material.
- Logo files, ideally with a transparent background — PNG, JPEG, GIF, WEBP, AVIF, or SVG all work.
- Font names, or a file/URL where the fonts can be downloaded.
- A written content plan: which pages exist, what each one contains, and in what order — more useful than a finished visual layout, since it maps directly onto the blocks above.

## What's not useful

- A full custom frontend, built expecting to "plug into" AMS as a backend — there's nowhere for it to plug into, as explained above.
- Pixel-perfect mockups that assume a capability listed as not possible above (a one-off section background colour, a uniquely coloured heading, and so on) — these can't be reproduced exactly, so the design work is wasted.

## If your agency wants to host its own site

Some agencies prefer to design and host their own marketing site directly, with AMS running only the membership and logged-in parts of the experience.
This is possible using a [subdomain](glossary.md#subdomain):

- AMS runs on a subdomain of the client's domain, such as `members.example.org`, while your agency's own site uses the main domain.
- Your client's [DNS controller](glossary.md#dns-record) needs to add a DNS record pointing that subdomain at AMS — ask your client's provider for the exact record once you're ready.
- **Navigation isn't shared between the two sites.** Menus, header and footer links, and any branding changes have to be made in both places separately, since they're two independent websites, not one site split across two addresses.

## Questions?

If a design idea doesn't match what's described here, or you're not sure whether something is possible, ask your client to check with their [provider](glossary.md#provider) before you build it — much cheaper than finding out afterwards.
