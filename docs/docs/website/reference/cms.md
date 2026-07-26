# CMS

**Who this page is for:** client website admins — the volunteers who load content and run the day-to-day site.

The website uses a content management system (CMS) called [Wagtail](../../getting-started/glossary.md#cms) to allow editing of website content.
This includes:

- Editing page content
- Setting the association name and logo
- Managing menus
- Uploading images and documents

See [Tutorial 1: Orientation](../setup/orientation.md) for how to sign in and find the CMS, and [Tutorial 3: Your first pages](../setup/first-pages.md) for a step-by-step walkthrough of creating and publishing a page.

## Admin interface

The CMS can be accessed at the `/cms/` path.

## Page types

Pages in the CMS come in a few types:

- **Home page** — the top-level page for each enabled language. Your provider creates this for you; it starts empty. See [Tutorial 3: Your first pages](../setup/first-pages.md) for how to add content to it.
- **Content page** — the type used for everything else: About, Contact, and any other page you create. Each content page can be:
    - **Public** or **Members only** — a members-only page is hidden from visitors without an active membership.
    - **Structure only** — a page that redirects straight to its first child page, rather than showing its own content. Useful for a parent page that exists only to group other pages in the menu.
- **Article** — an optional page type for blog-style posts with a publication date, summary, and cover image, listed on an articles index page. Not covered by the tutorial series.

## Content blocks

Both Home and Content pages are built from content blocks, added one at a time in the **Body** section of the page editor.
Content pages and Home pages share most blocks (Heading, Paragraph, Lead paragraph, Image, Image grid, Image carousel, Horizontal separator, Timeline, Embed, Columns, Full width section), with a few extras only available on one or the other:

- **Home page only:** Title block (the large hero-style heading — see [Tutorial 2: Branding & theme](../setup/branding-theme.md)), Recent articles.
- **Content page only:** Contact Form (see [Tutorial 3: Your first pages](../setup/first-pages.md)).

## Images and documents

Uploaded images and documents are shared across every page and every language, rather than belonging to one page.
Find them under **Images** and **Documents** in the CMS sidebar — a block that needs an image or a file (an Image block, a document link inside a Paragraph block, and so on) lets you upload a new one or choose an existing one from this shared library.

## Reserved URL Patterns

A page directly under Home can't use certain words as its web address (its slug, normally set automatically from the page's title) — these are already used by other parts of the website. The main ones are:

- `/admin/` - Django admin
- `/accounts/` - User authentication (sign in, sign up, password reset)
- `/billing/` - Billing application
- `/cms/` - Content management system
- `/cms-documents/` - CMS document library
- `/events/` - Events application (only reserved if the events feature is enabled)
- `/forum/` - Forum application
- `/organisations/` - Organisation management
- `/resources/` - Resources application (only reserved if the resources feature is enabled)
- `/terms/` - Terms and conditions
- `/users/` - User and membership management

There are a few dozen more, less obvious ones (shorter technical words already used somewhere inside the site) — rather than list every one, the CMS checks for you automatically and shows a clear error if a page's slug collides with one, so you'll only need this list if you want to understand why an error appeared.

See [Tutorial 3: Your first pages, "Create more pages the same way"](../setup/first-pages.md#create-more-pages-the-same-way) for where this comes up in practice.
Pages nested more deeply (for example, a page under About) are not affected by this restriction — only direct children of Home are checked.

## Menus

When creating menus within the CMS, you may want to link to a page that is not created in the CMS, but a different part of the website.
You can use the following URLs within the 'External URL' field on a menu item to link to the following pages:

- Discourse forum = `/forum/` - This will automatically redirect visitors to the forum with proper authentication. See [Tutorial 7: Forum, "Let members find the forum"](../setup/forum.md#let-members-find-the-forum) for why this is the recommended way to link to your forum.
- Terms and Conditions = `/terms/` - This displays all current terms and policies.

See [Tutorial 4: Navigation & menus](../setup/navigation-menus.md) for a full walkthrough of adding pages and links to your menus.
