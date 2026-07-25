#!/usr/bin/env node
// Regenerates every screenshot in manifest.json against a local instance seeded
// by seed.sh (an empty skeleton site, not `sample_data`). Run inside the node
// container: `npm run docs:screenshots`.
// See docs/docs/developer/docs-conventions.md ("How to regenerate screenshots")
// for the seeding prerequisites.

import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "..", "..");
const IMAGES_ROOT = path.join(REPO_ROOT, "docs", "docs", "images");
const MANIFEST_PATH = path.join(__dirname, "manifest.json");

const BASE_URL = process.env.DOCS_SCREENSHOTS_BASE_URL ?? "http://localhost:3000";
const VIEWPORT = { width: 1280, height: 800 };
const DEVICE_SCALE_FACTOR = 2;
const DEMO_ORG_NAME = "Mathematics Teachers Association";
const DEMO_LOGO_TITLE = "Mathematics Teachers Association logo";
const DEMO_LOGO_FIXTURE = path.join(__dirname, "fixtures", "demo-logo.png");
const THEME_PRIMARY_BRAND = "#7b1fa2";
const THEME_FONT_BRAND = '"Poppins", "Helvetica Neue", sans-serif';
const HOME_TITLE_TEXT = "Welcome to Mathematics Teachers Association";
const HOME_TAGLINE_TEXT =
  "Supporting maths teachers with resources, events, and a community.";
const ABOUT_BODY_TEXT =
  "Mathematics Teachers Association supports maths teachers across the country with resources, events, and a community forum.";
const CONTACT_RECIPIENT_EMAIL = "hello@mathematicsteachers.example";
const OUR_STORY_BODY_TEXT =
  "Mathematics Teachers Association was founded by volunteer teachers who wanted an easier way to share resources.";
const FOOTER_COLUMN1_TITLE = "Footer column 1";
const FOOTER_COLUMN1_HEADING = "Quick links";
const FOOTER_EXTERNAL_URL = "https://example.org";
const FOOTER_EXTERNAL_LINK_TEXT = "Curriculum resources";
const FOOTER_COLUMN2_TITLE = "Footer column 2";
const FOOTER_COLUMN2_HEADING = "Get in touch";
const MAORI_ABOUT_TITLE = "Mō mātou";
const MAORI_ABOUT_BODY = "Nau mai, haere mai ki tō mātou paetukutuku.";
const MAORI_ABOUT_SLUG = "about";
const MEMBERSHIP_OPTION_NAME = "Standard membership";
const MEMBERSHIP_OPTION_DURATION_NUM = "1";
const MEMBERSHIP_OPTION_COST = "40";
const MEMBERSHIP_OPTION_INVOICE_REFERENCE = "MTA Membership";
const MAILPIT_ORIGIN = "http://mailpit:8025";

function readEnvFile(relPath) {
  const text = fs.readFileSync(path.join(REPO_ROOT, relPath), "utf8");
  const values = {};
  for (const line of text.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const idx = trimmed.indexOf("=");
    if (idx === -1) continue;
    values[trimmed.slice(0, idx)] = trimmed.slice(idx + 1);
  }
  return values;
}

const localEnv = readEnvFile(".envs/.local/django.ini");
const ADMIN_EMAIL = localEnv.SAMPLE_DATA_ADMIN_EMAIL;
const ADMIN_PASSWORD = localEnv.SAMPLE_DATA_ADMIN_PASSWORD;

// django-debug-toolbar renders live query/timing stats that differ on every
// request, which would make screenshots non-deterministic. Hide it before
// every capture. The Wagtail preview panel (first used in the Your first
// pages tutorial) loads the public page in its own iframe, a separate
// browsing context with its own #djDebugRoot -- page.addStyleTag() alone only
// reaches the top-level document, so it's applied to every frame, not just
// the main one. Found by inspecting a captured preview screenshot and seeing
// the toolbar's panel (already expanded, not just its closed handle)
// covering the preview content.
//
// Wagtail's admin footer also shows a "You have unsaved edits" warning,
// via a Stimulus controller that dirties on a debounce rather than
// instantly (confirmed live via manual timing, ~700-800ms after a field
// change). The first fix tried was waiting for it to *appear* before
// capturing, on the theory that showing it consistently beats racing it --
// but that broke worse: in the actual headless capture browser (not the
// interactive one used to first observe the timing), the warning never
// appeared at all within a generous 30s wait on 10 of 14 navigation-menus
// steps, all timing out. Hiding it instead -- the same "remove the
// nondeterministic chrome element" fix as #djDebugRoot above, not a new
// approach -- sidesteps the question of why the two browser contexts
// behave differently, and matches every tutorial's actual scope: none of
// them are teaching what this warning means.
async function prepareForCapture(page) {
  for (const frame of page.frames()) {
    await frame
      .addStyleTag({
        content:
          "#djDebugRoot { display: none !important; } [data-controller='w-messages'] { display: none !important; }",
      })
      .catch(() => {});
  }
}

const MEDIA_LOCALHOST_ORIGIN = "http://localhost:9000";
const MEDIA_CONTAINER_ORIGIN = "http://minio:9000";

// Uploaded media (images, documents) gets a URL under
// DJANGO_MEDIA_PUBLIC_CUSTOM_DOMAIN=localhost:9000/..., which is correct for
// a browser running on the host machine, but this suite's browser runs
// inside the `node` container, where "localhost" means the node container
// itself -- nothing listens on port 9000 there, only on the host and inside
// the `minio` container. Without this, any page showing a real uploaded
// image (e.g. branding-theme's logo) would capture a broken-image icon
// instead. Reroute those specific requests to `minio`, the docker-network
// hostname the `node` container can actually reach.
async function proxyMinioMedia(page) {
  await page.route(`${MEDIA_LOCALHOST_ORIGIN}/**`, async (route) => {
    const url = new URL(route.request().url());
    const target = `${MEDIA_CONTAINER_ORIGIN}${url.pathname}${url.search}`;
    const response = await route.fetch({ url: target });
    await route.fulfill({ response });
  });
}

async function login(page) {
  await page.goto(`${BASE_URL}/en/accounts/login/`);
  await page.fill("#id_login", ADMIN_EMAIL);
  await page.fill("#id_password", ADMIN_PASSWORD);
  await page.click("button[type=submit], input[type=submit]");
  await page.waitForLoadState("networkidle");
}

async function openAssociationSettings(page) {
  await page.goto(`${BASE_URL}/cms/settings/cms/associationsettings/`);
  await page.waitForLoadState("networkidle");
}

async function openThemeSettings(page) {
  await page.goto(`${BASE_URL}/cms/settings/cms/themesettings/`);
  await page.waitForLoadState("networkidle");
}

// Branding & theme (tutorial 2) capture steps mutate real site state (the
// association logo, the primary colour) instead of just reading it, so
// unlike the read-only orientation steps, they only produce correct
// screenshots when run in `manifest.json`'s declared order against a
// just-seeded site, in one `docs:screenshots` invocation — see the ordering
// note in docs-conventions.md's "Idempotent capture steps" bullet.

// Opens the association logo chooser (assumed currently unchosen) and
// switches to its Upload tab, waiting for the modal's own async-loaded
// content to be ready before returning it. Wagtail's chooser dialog fetches
// its Search/Upload tab markup after the "Choose an image" click, and acting
// before that fetch resolves (fine for a human, too fast for a script with
// no pause between actions) intermittently raced Wagtail's own tab-switching
// JS in testing -- waiting for the Search tab (the default-open one) to be
// visible first avoids that race.
async function openLogoUploadTab(page) {
  await page.locator("#id_association_logo-chooser [data-chooser-action-choose]").click();
  const modal = page.locator('[role="dialog"][aria-hidden="false"]');
  await modal.getByRole("tab", { name: "Search" }).waitFor({ state: "visible" });
  await modal.getByRole("tab", { name: "Upload" }).click();
  await modal.locator("#id_image-chooser-upload-title").waitFor({ state: "visible" });
  return modal;
}

// Opens the Upload tab, uploads the fixture logo, and waits for the chooser
// widget to show it as chosen. Does not save the parent form.
//
// Wagtail's own duplicate-image detection intercepts this upload from the
// second branding-theme capture step onward: the fixture file is byte-
// identical every time, and earlier steps in this same run (e.g.
// brandingLogoSelected) already uploaded it once, so Wagtail shows a "your
// new image seems to be a duplicate" interstitial with "Use new image" /
// "Use existing and delete new" links instead of closing the modal straight
// away. Always choosing "Use new image" keeps behaviour identical to the
// non-duplicate path (a freshly chosen image) rather than reusing an older
// step's image object.
async function uploadDemoLogo(page) {
  const modal = await openLogoUploadTab(page);
  await modal.locator("#id_image-chooser-upload-title").fill(DEMO_LOGO_TITLE);
  await modal.locator("#id_image-chooser-upload-file").setInputFiles(DEMO_LOGO_FIXTURE);
  await modal.getByRole("button", { name: "Upload" }).click();

  const useNewImage = modal.getByRole("link", { name: "Use new image" });
  const isDuplicate = await useNewImage
    .waitFor({ state: "visible", timeout: 3000 })
    .then(() => true)
    .catch(() => false);
  if (isDuplicate) {
    await useNewImage.click();
  }

  await page.waitForFunction(
    (title) =>
      document.querySelector("#id_association_logo-title")?.textContent.trim() === title,
    DEMO_LOGO_TITLE,
  );
}

// Your first pages (tutorial 3) capture steps create and edit real pages, so
// like branding & theme's steps, they only produce correct screenshots when
// run in manifest.json's declared order against a just-seeded site -- see
// docs-conventions.md's "Ordering for capture steps that change site state"
// bullet.

// The English home page's ID depends on AMS_ENABLED_LANGUAGES's order (see
// docs-conventions.md's "Screenshot content depends on AMS_ENABLED_LANGUAGES"
// note) -- setup_cms creates one HomePage per configured language, in that
// order, so which numeric page ID ends up English varies with the env var.
// Resolved once per run by reading the page explorer, rather than
// hard-coding a page ID that would silently point at the wrong (Māori) home
// page in a differently-configured environment.
let englishHomePageId;
async function getEnglishHomePageId(page) {
  if (englishHomePageId) return englishHomePageId;
  await page.goto(`${BASE_URL}/cms/pages/1/`);
  await page.waitForLoadState("networkidle");
  const englishRow = page.getByRole("row").filter({ hasText: "English" });
  const homeLink = englishRow.getByRole("link", { name: "Home", exact: true });
  const href = await homeLink.getAttribute("href");
  englishHomePageId = href.match(/\/pages\/(\d+)\//)[1];
  return englishHomePageId;
}

async function openHomeEdit(page) {
  const homeId = await getEnglishHomePageId(page);
  await page.goto(`${BASE_URL}/cms/pages/${homeId}/edit/`);
  await page.waitForLoadState("networkidle");
}

// Languages & translations (tutorial 5) needs the Te Reo Māori Home page's
// ID, the same way getEnglishHomePageId() needs the English one -- resolved
// at runtime rather than hard-coded, for the same reason (it depends on
// AMS_ENABLED_LANGUAGES's order in this environment).
let maoriHomePageId;
async function getMaoriHomePageId(page) {
  if (maoriHomePageId) return maoriHomePageId;
  await page.goto(`${BASE_URL}/cms/pages/1/`);
  await page.waitForLoadState("networkidle");
  const maoriRow = page.getByRole("row").filter({ hasText: "Māori" });
  const homeLink = maoriRow.getByRole("link", { name: "Home", exact: true });
  const href = await homeLink.getAttribute("href");
  maoriHomePageId = href.match(/\/pages\/(\d+)\//)[1];
  return maoriHomePageId;
}

async function openAddChildPage(page, parentId) {
  await page.goto(`${BASE_URL}/cms/pages/${parentId}/add_subpage/`);
  await page.waitForLoadState("networkidle");
}

// Starts a new Content page under parentId and fills in its title. Wagtail
// assigns the new page a real ID and switches the URL from .../add/... to
// .../<id>/edit/ as soon as the first body block is inserted (observed
// directly, not assumed) -- callers read that ID back off page.url() after
// inserting a block, rather than guessing it.
async function createContentPage(page, parentId, title) {
  await openAddChildPage(page, parentId);
  await page.getByRole("link", { name: "Content page", exact: true }).click();
  await page.waitForLoadState("networkidle");
  await page.getByRole("textbox", { name: "Title*" }).fill(title);
}

// Uses the *last* "Insert a block" button, not the first, so this works both
// to start an empty Body (only one such button exists, first === last) and
// to append a further block after one already inserted (e.g. a tagline
// after a Title block) -- the first button in that second case would insert
// *before* the existing block instead of after it.
async function insertBodyBlock(page, blockName) {
  await page.getByRole("button", { name: "Insert a block" }).last().click();
  await page.getByRole("option", { name: blockName, exact: true }).click();
}

// Draftail (the rich text editor behind paragraph_block/lead_paragraph_block)
// renders a contenteditable div whose own React state -- not just its DOM
// text -- is what gets serialized on save. locator.fill() sets the DOM text
// directly and looked like it worked when inspected live, but saved an empty
// value: Draftail never saw real input events, so its internal EditorState
// stayed empty. pressSequentially() dispatches real keystrokes instead,
// which Draftail does pick up. Found by checking the saved page content
// directly (it was blank) after fill() appeared to work in the browser.
// Targets the *last* matching textbox, not the only one -- when a Title
// block sits earlier in the same Body (its own Text field only reachable
// while its "Title Settings" panel is expanded), the block being filled here
// is always the most recently inserted one.
//
// Typing alone isn't enough, either: Draftail debounces syncing its React
// state to the hidden `body-<n>-value[-text]` input the form actually saves
// from, so saving immediately after typing can still race that debounce and
// persist an empty value -- even though the typed text is already visible
// on screen and readable back via textContent(). A fixed pause after typing
// (tried first) was flaky: it happened to be long enough in some runs and
// not others, especially on the home page where a Title block's extra
// widgets add more going on before this field's own sync settles. Instead
// of guessing a pause, wait for the actual hidden input to contain the
// typed text -- a deterministic signal instead of a timing guess.
async function fillBodyText(page, text) {
  const textbox = page.getByRole("region", { name: "Body" }).getByRole("textbox").last();
  await textbox.click();
  await textbox.pressSequentially(text);
  await page.waitForFunction(
    (expected) => {
      const inputs = document.querySelectorAll('input[type="hidden"][id^="body-"]');
      return Array.from(inputs).some((el) => el.value && el.value.includes(expected));
    },
    text,
    { timeout: 5000 },
  );
}

// The Title block (Home page only) wraps a plain TextBlock, not Draftail --
// fill() works correctly here (confirmed by checking the saved value), no
// pressSequentially() needed. Its "Title Settings" sub-panel starts
// collapsed (Meta.collapsed = True on TypographyBlock), so the Text field
// isn't present/focusable until that panel is expanded. Assumes the Title
// block is the first block in Body (block index 0), true whenever it's the
// first block inserted into a fresh page -- the only way this tutorial uses
// it.
async function fillTitleBlockText(page, text) {
  const panelId = "block_group-body-0-value-title-section";
  await page.locator(`#${panelId} button[data-panel-toggle]`).click();
  await page.locator(`#${panelId}`).getByRole("textbox", { name: "Text*" }).fill(text);
}

// Wagtail auto-fills the Slug field (Promote tab) from the page title, and
// -- found live while building the languages & translations tutorial, the
// first capture step that needs to *override* the auto-filled slug rather
// than accept it -- a value set with locator.fill() is silently reverted
// back to the auto-generated slug the next time a StreamField block is
// inserted elsewhere on the page. Confirmed by direct testing: filling the
// slug, then inserting a body block, read the slug field's value back as
// the plain auto-slugified title again, as if the fill() had never
// happened. locator.fill() sets the input's value without the field's own
// "w-slug" Stimulus controller seeing a real edit, so it doesn't count as
// user input the same way typed keystrokes do.
// Real keystrokes (pressSequentially) survive this, but the fix that
// actually matters is doing the slug edit *last*, after every content
// block is already in place -- this function is only ever called right
// before publishing, never before inserting a block.
async function setPageSlug(page, slug) {
  await page.getByRole("tab", { name: "Promote" }).click();
  const field = page.getByRole("textbox", { name: "Slug*" });
  await field.click();
  await field.press("Control+a");
  await field.press("Backspace");
  await field.pressSequentially(slug, { delay: 20 });
  await page.waitForFunction(
    (expected) => document.querySelector("#id_slug")?.value === expected,
    slug,
    { timeout: 5000 },
  );
}

async function saveDraft(page) {
  await page.getByRole("button", { name: "Save draft" }).click();
  await page.waitForLoadState("networkidle");
}

async function publishViaMoreActions(page) {
  await page.getByRole("button", { name: "More actions" }).click();
  await page.getByRole("button", { name: "Publish" }).click();
  await page.waitForLoadState("networkidle");
}

function pageIdFromEditUrl(page) {
  return page.url().match(/\/pages\/(\d+)\/edit\/?/)[1];
}

// The Wagtail admin's CSS sets `scroll-behavior: smooth` (used for its
// minimap anchor links), so a plain scrollIntoView() animates over several
// hundred ms instead of jumping immediately -- a screenshot taken right
// after would still show the pre-scroll position. Found by instrumenting a
// capture step: two boundingBox() reads immediately before/after
// scrollIntoView() were identical, only a real wait or an explicit instant
// scroll fixed it. `behavior: "instant"` sidesteps the animation instead of
// guessing a wait long enough to outlast it.
async function scrollIntoViewInstantly(locator) {
  await locator.evaluate((el) => el.scrollIntoView({ block: "center", behavior: "instant" }));
}

// Home's parent is Root, so publishing it lands the confirmation banner on
// the Root explorer -- which also lists the Māori home page and Wagtail's
// own unrelated "Welcome to your new Wagtail site!" leftover page (see
// docs-conventions.md's AMS_ENABLED_LANGUAGES note; this is the page-tree
// version of that same multi-language dev environment quirk). None of that
// is meaningful to a first-time reader following the tutorial with a single
// language, and re-navigating to a cleaner page would lose the one-time
// flash message this screenshot exists to show. Hiding the unrelated rows
// in place keeps the real "published" confirmation while dropping the
// confusing detail, and is still fully scripted/regenerable (not a manual
// annotation -- see docs-conventions.md's annotated-image exception, which
// this isn't).
async function hideUnrelatedRootPages(page) {
  await page.evaluate(() => {
    document.querySelectorAll("table tbody tr").forEach((row) => {
      const text = row.textContent || "";
      if (text.includes("Māori") || text.includes("Welcome to your new Wagtail site")) {
        row.style.display = "none";
      }
    });
    // Root's own explanatory callout ("The root level is where you can add
    // new sites...") is Wagtail-internal jargon a first-time reader doesn't
    // need and could easily misread as "your home page isn't accessible yet"
    // -- hide its containing block same as the unrelated rows above.
    document.querySelectorAll("p").forEach((p) => {
      if ((p.textContent || "").includes("The root level is where")) {
        (p.closest("div") ?? p).style.display = "none";
      }
    });
  });
}

// Set by firstPagesAboutContent/firstPagesContactFormBlock for the publish
// steps just after them in manifest.json order to read back.
let aboutPageId;
let contactPageId;

// Navigation & menus (tutorial 4) builds a Main menu around the About and
// Contact pages "Your first pages" (tutorial 3) already created and
// published, and adds one more child page under About to demonstrate an
// automatic dropdown -- these steps only make sense to run after the
// firstPages* steps earlier in manifest.json's order, the same
// same-run-dependency pattern branding/first-pages steps already rely on.

async function openMainMenu(page) {
  await page.goto(`${BASE_URL}/cms/wagtailmenus/mainmenu/`);
  await page.waitForLoadState("networkidle");
}

// Adds a "Link to an internal page" menu item and picks `title` via the
// page chooser. The chooser always opens at Root, regardless of any earlier
// item's selection -- every page this tutorial adds to the menu (About,
// Contact) is a direct child of the English home page, so a fixed two-click
// drill-down (Explore Home, then pick the page) works for both without
// per-page navigation logic. Only ever one "Choose a page" button is
// visible at a time: once a page is picked, that item's button becomes a
// "chosen" state instead, so this doesn't need to disambiguate between
// items the way insertBodyBlock's `.last()` does.
//
// Selecting a page closes the modal with a fade-out transition rather than
// removing it immediately -- a screenshot taken right after the click (as
// found live, not assumed) captured the dialog mid-fade, semi-transparent
// and overlapping the page underneath instead of the clean "page chosen"
// state the step exists to show. Waiting for the modal to actually reach
// Playwright's "hidden" state (Bootstrap sets display: none once the fade
// finishes) sidesteps the animation the same way scrollIntoView's
// `behavior: "instant"` sidesteps its own transition, rather than guessing
// a pause long enough to outlast it.
//
// Scoped to `.modal.fade` specifically, not every `[role="dialog"]" -- the
// CMS admin also has a permanently-present (usually hidden) keyboard
// shortcuts dialog with its own aria-hidden attribute, and matching both
// makes Playwright's strict mode reject the locator as ambiguous (found
// live, not assumed, when an earlier version used the broader selector).
//
// A second, separate remnant even after the modal itself is hidden: Bootstrap
// also adds a `.modal-backdrop` element (the dimming overlay) and a
// `modal-open` class on <body> while the modal is showing, and removes both
// slightly *after* the modal's own fade finishes, not at the same instant --
// confirmed live by counting `.modal-backdrop` immediately after the modal
// reached "hidden" (still 1) versus after also waiting for it to detach
// (0). Without this second wait, a capture right after modal.waitFor()
// still shows the whole page dimmed under a leftover backdrop.
async function addMainMenuItem(page, title) {
  await page.getByRole("button", { name: "Add menu item" }).click();
  await page.getByRole("button", { name: "Choose a page" }).click();
  const modal = page.locator('.modal.fade[role="dialog"]');
  await modal.getByRole("link", { name: "Explore" }).click();
  await modal.getByRole("link", { name: title, exact: true }).click();
  await modal.waitFor({ state: "hidden" });
  await page.locator(".modal-backdrop").waitFor({ state: "detached" });
  // Clicking "Add menu item" appends a new panel without reliably scrolling
  // to it -- confirmed non-deterministic live, not assumed: two identical
  // runs of the same capture step landed at different scroll positions (one
  // showed the page from the top, the other already scrolled to the new
  // item), a real "visually identical" failure per docs-conventions.md's
  // regeneration requirement, not the usual harmless sub-pixel jitter.
  // Scrolling the just-added item into view explicitly, the same fix
  // pattern as bullet 12's `scroll-behavior: smooth`, makes every capture
  // land on the same framing regardless of where the page happened to be
  // scrolled beforehand.
  const lastItemRegion = page.locator('[id^="inline_child_menu_items-"][id$="-panel-section"]').last();
  await scrollIntoViewInstantly(lastItemRegion);
}

async function saveMainMenu(page) {
  await page.getByRole("button", { name: "Save" }).click();
  await page.waitForLoadState("networkidle");
}

// Adds a content-page child of an existing ContentPage (About), unlike
// createContentPage's use under Home. ContentPage.subpage_types only
// allows further ContentPage children (ams/cms/models/pages.py), so with
// exactly one allowed type Wagtail skips the page-type chooser and opens
// the add form directly -- confirmed live, not assumed, since it differs
// from createContentPage's chooser-then-click-"Content page" flow under
// Home, which allows more than one child type.
async function createChildContentPage(page, parentId, title) {
  await openAddChildPage(page, parentId);
  await page.getByRole("textbox", { name: "Title*" }).fill(title);
}

// Footer links (also part of tutorial 4) use Flat menus, a separate
// wagtailmenus model from the Main menu but the same underlying
// InlinePanel machinery for its items -- WAGTAILMENUS_MAIN_MENU_ITEMS_RELATED_NAME
// and WAGTAILMENUS_FLAT_MENU_ITEMS_RELATED_NAME both default to 'menu_items'
// (confirmed in wagtailmenus/conf/defaults.py, not assumed), so
// addMainMenuItem's "Add menu item" / "Choose a page" flow and its
// `inline_child_menu_items-*-panel-section` selector work unmodified here
// too -- reused directly below rather than duplicated.

async function openAddFlatMenu(page) {
  await page.goto(`${BASE_URL}/cms/wagtailmenus/flatmenu/add/`);
  await page.waitForLoadState("networkidle");
}

// Fills the flat menu's own details (Title, Site, Handle, Heading) --
// separate from the menu *items* addMainMenuItem/addCustomUrlMenuItem add
// afterwards. Site has no default: left on the blank "---------" option,
// Save fails validation (confirmed live), so it's always selected
// explicitly here rather than assumed to already be right.
async function fillFlatMenuDetails(page, { title, handle, heading }) {
  await page.getByRole("textbox", { name: "Title*" }).fill(title);
  await page.getByLabel("Site*").selectOption({ label: "English Site [default]" });
  await page.getByLabel("Handle*").selectOption({ label: handle });
  await page.getByRole("textbox", { name: "Heading" }).fill(heading);
}

async function saveFlatMenu(page) {
  await page.getByRole("button", { name: "Save" }).click();
  await page.waitForLoadState("networkidle");
}

// Adds a "Link to a custom URL" item -- the external-link counterpart to
// addMainMenuItem's internal-page flow, used by both the Main menu and
// Flat menu forms. No page chooser modal is involved, so none of
// addMainMenuItem's modal-close/backdrop waits apply here; the only
// determinism risk carried over is the same unreliable auto-scroll
// addMainMenuItem already works around, so this scrolls the new item into
// view the same way.
async function addCustomUrlMenuItem(page, url, linkText) {
  await page.getByRole("button", { name: "Add menu item" }).click();
  const lastItem = page.locator('[id^="inline_child_menu_items-"][id$="-panel-section"]').last();
  await lastItem.getByRole("textbox", { name: "Link to a custom URL" }).fill(url);
  await lastItem.getByRole("textbox", { name: "Link text" }).fill(linkText);
  await scrollIntoViewInstantly(lastItem);
}

// Memberships (tutorial 6). Membership options are managed in the Django
// admin, not the CMS -- these steps build on each other in the same way
// branding/first-pages' state-changing steps do: this tutorial's own option
// and application only exist once earlier steps in manifest.json's order
// have created them in this run.

async function openMembershipOptionAdd(page) {
  await page.goto(`${BASE_URL}/admin/memberships/membershipoption/add/`);
  await page.waitForLoadState("networkidle");
}

// Individual is already the default selection for Type (the first
// MembershipOptionType choice), so this only needs to fill the fields that
// don't already have a usable default.
async function fillMembershipOptionForm(page) {
  await page.getByRole("textbox", { name: "Name:" }).fill(MEMBERSHIP_OPTION_NAME);
  await page.locator("#id_duration_0").fill(MEMBERSHIP_OPTION_DURATION_NUM);
  await page.locator("#id_duration_1").selectOption("Years");
  await page.getByRole("spinbutton", { name: "Cost:" }).fill(MEMBERSHIP_OPTION_COST);
  await page
    .getByRole("textbox", { name: "Invoice Reference:" })
    .fill(MEMBERSHIP_OPTION_INVOICE_REFERENCE);
}

// Scoped to "Save", not "Save and add another"/"Save and continue editing" --
// Django admin's add/change forms always offer all three.
async function saveAdminForm(page) {
  await page.getByRole("button", { name: "Save", exact: true }).click();
  await page.waitForLoadState("networkidle");
}

async function openApplyIndividual(page) {
  await page.goto(`${BASE_URL}/en/users/memberships/apply-individual/`);
  await page.waitForLoadState("networkidle");
}

// PricingCardsRadio (ams/templates/utils/crispy_forms/pricing_card.html)
// renders each option as a real <input class="btn-check"> paired with a
// <label class="pricing-card">, Bootstrap's checked-button pattern -- the
// input itself is visually hidden, so clicking/checking it directly always
// resolves to whatever's visually on top at its coordinates (the card's own
// header, or the page's fixed navbar) rather than actually selecting it.
// Clicking the associated <label> instead is what a real visitor's click
// lands on, and toggles the input via the native for= association.
// This tutorial's site only ever has the one membership option this same
// run created earlier, so the first (only) pricing card is always the right
// one -- the same "only one exists" simplification addMainMenuItem relies
// on for its own single-button case.
async function selectFirstMembershipOption(page) {
  const label = page.locator("label.pricing-card").first();
  await scrollIntoViewInstantly(label);
  await label.click();
}

async function registerMembership(page) {
  await page.getByRole("button", { name: "Register membership" }).click();
  await page.waitForLoadState("networkidle");
}

// Deletes every message Mailpit is currently holding via its HTTP API, called
// from the script's own Node process (not the browser) -- this doesn't need
// a page open, just a network call from inside the same node container,
// which can already reach every other compose service by name.
async function clearMailpit() {
  await fetch(`${MAILPIT_ORIGIN}/api/v1/messages`, { method: "DELETE" });
}

// Finds the ID of the one message from a given sender address, via Mailpit's
// own HTTP API (not the browser) -- used to open a specific message directly
// by its /view/<id> URL rather than picking through the inbox list on
// screen. Assumes clearMailpit() ran earlier in this same step, so exactly
// the messages a single action produced are present.
async function getMailpitMessageIdByFrom(fromAddress) {
  const res = await fetch(`${MAILPIT_ORIGIN}/api/v1/messages`);
  const data = await res.json();
  const match = data.messages.find((m) => m.From?.Address === fromAddress);
  return match ? match.ID : null;
}

// Finds how far down an iframe's real (non-whitespace) text content extends,
// in the iframe's own local coordinate space. Mailpit's #preview-html iframe
// (the email's rendered HTML) is forced to a fixed height regardless of the
// actual email's length -- MJML-generated emails set html/body to fill their
// container for consistent background colour across email clients, so the
// iframe's own scrollHeight is *not* a usable signal for where the visible
// content actually ends. Walking every text node and taking the lowest one's
// bounding rect finds the real answer regardless of surrounding layout
// wrappers or background-only filler elements.
async function getIframeContentBottom(page, iframeSelector) {
  return await page.evaluate((sel) => {
    const el = document.querySelector(sel);
    const doc = el.contentDocument;
    const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT);
    let node;
    let maxBottom = 0;
    while ((node = walker.nextNode())) {
      if (!node.textContent.trim()) continue;
      const range = doc.createRange();
      range.selectNodeContents(node);
      const rect = range.getBoundingClientRect();
      if (rect.bottom > maxBottom) maxBottom = rect.bottom;
    }
    return maxBottom;
  }, iframeSelector);
}

// This run's only Membership: Individual record, so the single result row's
// own link is always the right one to open -- the same "only one exists"
// simplification selectFirstMembershipOption relies on above.
async function openFirstIndividualMembership(page) {
  await page.goto(`${BASE_URL}/admin/memberships/individualmembership/`);
  await page.waitForLoadState("networkidle");
  await page.getByRole("link", { name: "Admin Account" }).click();
  await page.waitForLoadState("networkidle");
}

// Sets Approved datetime to now via the admin's own "Today"/"Now" quick-fill
// links, scoped to the approved_datetime field row specifically -- Start
// date and Expiry date above it have their own identically-labelled "Today"
// links, so an unscoped page-wide lookup would be ambiguous.
async function approveViaTodayNow(page) {
  const field = page.locator(".field-approved_datetime");
  await field.getByRole("link", { name: "Today" }).click();
  await field.getByRole("link", { name: "Now" }).click();
}

// "Save and continue editing" (not "Save") deliberately, so the screenshot
// right after can show the same record's Status field having flipped from
// Pending to Active in place, rather than navigating away to prove it.
async function saveAdminFormContinueEditing(page) {
  await page.getByRole("button", { name: "Save and continue editing" }).click();
  await page.waitForLoadState("networkidle");
}

// Capture steps, keyed by the "step" field in manifest.json. Tutorial tasks
// (T13+) add their own steps and manifest entries here as they document
// each screen.
const steps = {
  async exampleLogin(page) {
    await page.goto(`${BASE_URL}/en/accounts/login/`);
    await page.waitForLoadState("networkidle");
  },

  async exampleDashboard(page) {
    await login(page);
    await page.goto(`${BASE_URL}/cms/`);
    await page.waitForLoadState("networkidle");
  },

  async orientationSignIn(page) {
    await page.goto(`${BASE_URL}/en/accounts/login/`);
    await page.waitForLoadState("networkidle");
  },

  async orientationYourAccount(page) {
    await login(page);
  },

  async orientationCmsDashboard(page) {
    await login(page);
    await page.goto(`${BASE_URL}/cms/`);
    await page.waitForLoadState("networkidle");
  },

  async orientationDjangoAdmin(page) {
    await login(page);
    await page.goto(`${BASE_URL}/admin/`);
    await page.waitForLoadState("networkidle");
  },

  async brandingAssociationSettings(page) {
    await login(page);
    await openAssociationSettings(page);
  },

  // Sets the demo organisation name through the CMS itself, the same way a
  // real client would -- this is the only place DEMO_ORG_NAME gets written,
  // now that seed.sh no longer seeds it directly. Every later capture step
  // in this run (and every screenshot after this one in manifest.json's
  // order) inherits the saved name; anything captured earlier still shows
  // setup_cms's placeholder, which is expected.
  async brandingAssociationName(page) {
    await login(page);
    await openAssociationSettings(page);
    await page.locator("#id_association_short_name").fill(DEMO_ORG_NAME);
    await page.locator("#id_association_long_name").fill(DEMO_ORG_NAME);
    await page.getByRole("button", { name: "Save" }).click();
    await page.waitForLoadState("networkidle");
  },

  async brandingUploadTab(page) {
    await login(page);
    await openAssociationSettings(page);
    await openLogoUploadTab(page);
  },

  async brandingLogoSelected(page) {
    await login(page);
    await openAssociationSettings(page);
    await uploadDemoLogo(page);
  },

  async brandingLogoSaved(page) {
    await login(page);
    await openAssociationSettings(page);
    await uploadDemoLogo(page);
    await page.getByRole("checkbox", { name: "Use logo in navbar" }).check();
    await page.getByRole("checkbox", { name: "Use logo in footer" }).check();
    await page.getByRole("button", { name: "Save" }).click();
    await page.waitForLoadState("networkidle");
  },

  // Relies on brandingLogoSaved (the manifest entry just before this one)
  // having already saved the logo earlier in this same run.
  async brandingLogoLive(page) {
    await login(page);
    await page.goto(`${BASE_URL}/en/`);
    await page.waitForLoadState("networkidle");
  },

  // Relies on running against a freshly-seeded site, before
  // brandingPrimarySaved changes the Primary colour later in this same run.
  async brandingThemeSettings(page) {
    await login(page);
    await openThemeSettings(page);
    await page.locator("#panel-primary-section").scrollIntoViewIfNeeded();
  },

  async brandingPrimarySaved(page) {
    await login(page);
    await openThemeSettings(page);
    const field = page.getByRole("textbox", { name: "Primary*", exact: true });
    await field.fill(THEME_PRIMARY_BRAND);
    await field.dispatchEvent("change");
    await page.getByRole("button", { name: "Save" }).click();
    await page.waitForLoadState("networkidle");
    await page.locator("#panel-primary-section").scrollIntoViewIfNeeded();
  },

  async brandingFontSaved(page) {
    await login(page);
    await openThemeSettings(page);
    const field = page.getByRole("textbox", { name: "Sans-serif font stack*", exact: true });
    await field.fill(THEME_FONT_BRAND);
    await field.dispatchEvent("change");
    await page.getByRole("button", { name: "Save" }).click();
    await page.waitForLoadState("networkidle");
    await page.locator("#panel-fonts-section").scrollIntoViewIfNeeded();
  },

  // Relies on running against a freshly-seeded site, before
  // firstPagesHomeTitle adds content to the home page later in this same
  // run.
  async firstPagesHomeEditEmpty(page) {
    await login(page);
    await openHomeEdit(page);
  },

  // Home page content starts with a Title block -- the page's main heading.
  // Saved on its own, separately from firstPagesHomeTagline below, not
  // merely for narrative pacing: see that step's comment for why this
  // actually has to be two separate saves, not one.
  async firstPagesHomeTitle(page) {
    await login(page);
    await openHomeEdit(page);
    await insertBodyBlock(page, "Title block");
    await fillTitleBlockText(page, HOME_TITLE_TEXT);
    await saveDraft(page);
  },

  // Adds a Lead paragraph block under the Title block as a short tagline.
  //
  // This has to be its own save, run against a page that already has the
  // Title block saved from firstPagesHomeTitle -- typing the tagline in the
  // *same* editing session as the Title block (insert Title, fill it,
  // insert Lead paragraph, fill that, save once) intermittently saved an
  // empty tagline, confirmed not to be the Draftail-sync race fillBodyText
  // already guards against (see its own comment): instrumenting the hidden
  // `body-1-value-text` input showed it briefly held the correct typed
  // value, then reset to `null` a few hundred ms later, well before Save
  // draft was even clicked -- something about the Title block's own widgets
  // (its colour pickers, its autosize textarea) appears to trigger a
  // StreamField-wide re-render that clobbers a sibling block's still-fresh,
  // unsaved edit. Reproduced this 3 runs in a row with the single-session
  // approach (each one failed a different way -- empty save, or the
  // deterministic hidden-field wait timing out entirely), then reproduced
  // *reliably* the fix of saving the Title block first and only inserting
  // the Lead paragraph afterward, against a page where the Title block is
  // now server-rendered/static rather than a live, still-mounting widget:
  // 4 runs in a row, correct every time. This changed the tutorial's own
  // step sequence to match (an extra numbered step, not just an
  // implementation detail): saving after each block is what's actually
  // reliable, so that's what the page now tells a real reader to do too.
  async firstPagesHomeTagline(page) {
    await login(page);
    await openHomeEdit(page);
    await insertBodyBlock(page, "Lead paragraph block");
    await fillBodyText(page, HOME_TAGLINE_TEXT);
    await saveDraft(page);
    // Same floating-bar overlap as firstPagesAboutContent/
    // firstPagesContactFormBlock below -- the Title block above it pushes
    // this field further down the page than a single block would.
    await scrollIntoViewInstantly(
      page.getByRole("region", { name: "Body" }).getByRole("textbox").last(),
    );
  },

  // Relies on firstPagesHomeTitle and firstPagesHomeTagline (the two
  // manifest entries just before this one) having already saved the title
  // and tagline as drafts earlier in this same run -- the edit form always
  // loads the latest revision, draft or published, so no re-typing is
  // needed here.
  async firstPagesHomePreview(page) {
    await login(page);
    await openHomeEdit(page);
    await page.getByRole("button", { name: "Toggle preview" }).click();
    const frame = page.frameLocator("iframe").first();
    await frame.getByText(HOME_TITLE_TEXT).waitFor({ state: "visible" });
  },

  async firstPagesHomePublished(page) {
    await login(page);
    await openHomeEdit(page);
    await publishViaMoreActions(page);
    await hideUnrelatedRootPages(page);
  },

  async firstPagesAddChildPage(page) {
    await login(page);
    const homeId = await getEnglishHomePageId(page);
    await openAddChildPage(page, homeId);
  },

  async firstPagesAboutContent(page) {
    await login(page);
    const homeId = await getEnglishHomePageId(page);
    await createContentPage(page, homeId, "About");
    await insertBodyBlock(page, "Paragraph block");
    await fillBodyText(page, ABOUT_BODY_TEXT);
    await saveDraft(page);
    aboutPageId = pageIdFromEditUrl(page);
    // The floating Save draft/More actions bar would otherwise cover the
    // bottom of the paragraph text -- see the same fix on
    // firstPagesContactFormBlock below.
    await scrollIntoViewInstantly(
      page.getByRole("region", { name: "Body" }).getByRole("textbox"),
    );
  },

  // Relies on firstPagesAboutContent (just before this one) having already
  // created and saved the About page as a draft earlier in this same run.
  async firstPagesAboutPublished(page) {
    await login(page);
    await page.goto(`${BASE_URL}/cms/pages/${aboutPageId}/edit/`);
    await page.waitForLoadState("networkidle");
    await publishViaMoreActions(page);
  },

  async firstPagesContactFormBlock(page) {
    await login(page);
    const homeId = await getEnglishHomePageId(page);
    await createContentPage(page, homeId, "Contact");
    await insertBodyBlock(page, "Contact Form");
    const recipientField = page.getByRole("textbox", { name: "Recipient email*" });
    await recipientField.fill(CONTACT_RECIPIENT_EMAIL);
    await saveDraft(page);
    contactPageId = pageIdFromEditUrl(page);
    // The floating Save draft/More actions bar sits over the bottom of the
    // viewport; scrollIntoViewIfNeeded() alone would land the field right
    // behind it (nearest-edge scrolling), so centre it instead.
    await scrollIntoViewInstantly(recipientField);
  },

  // Relies on firstPagesContactFormBlock (just before this one) having
  // already created and saved the Contact page as a draft earlier in this
  // same run.
  async firstPagesContactLive(page) {
    await login(page);
    await page.goto(`${BASE_URL}/cms/pages/${contactPageId}/edit/`);
    await page.waitForLoadState("networkidle");
    await publishViaMoreActions(page);
    await page.goto(`${BASE_URL}/en/contact/`);
    await page.waitForLoadState("networkidle");
  },

  async navigationMainMenuEmpty(page) {
    await login(page);
    await openMainMenu(page);
  },

  // The menu editor always starts from whatever's saved in the database, so
  // until navigationItemsSaved below actually saves, this and the next step
  // re-add About (and, for the next step, Contact) from scratch each time --
  // there's nothing yet to load.
  async navigationAboutItemAdded(page) {
    await login(page);
    await openMainMenu(page);
    await addMainMenuItem(page, "About");
  },

  async navigationContactItemAdded(page) {
    await login(page);
    await openMainMenu(page);
    await addMainMenuItem(page, "About");
    await addMainMenuItem(page, "Contact");
  },

  async navigationItemsSaved(page) {
    await login(page);
    await openMainMenu(page);
    await addMainMenuItem(page, "About");
    await addMainMenuItem(page, "Contact");
    await saveMainMenu(page);
  },

  // Relies on navigationItemsSaved (just before this one) having already
  // saved the About and Contact menu items earlier in this same run.
  async navigationMenuLive(page) {
    await login(page);
    await page.goto(`${BASE_URL}/en/`);
    await page.waitForLoadState("networkidle");
  },

  // Adds "Our story" as a child of About, purely to demonstrate that a
  // linked page with its own live children automatically becomes a
  // dropdown -- the same createChildContentPage/fillBodyText/publish
  // pattern first-pages.md's About and Contact steps already established
  // for creating and publishing a page. Reuses aboutPageId, set by
  // firstPagesAboutContent earlier in this same run. Publishing a non-root
  // page lands on its *parent's* page listing (confirmed live: publishing a
  // child of About redirects to About's own listing, the same way
  // publishing About itself redirected to Home's listing in
  // firstPagesAboutPublished) -- no extra navigation needed after
  // publishViaMoreActions for the screenshot to show "Our story" listed
  // under About.
  async navigationAboutChildAdded(page) {
    await login(page);
    await createChildContentPage(page, aboutPageId, "Our story");
    await insertBodyBlock(page, "Paragraph block");
    await fillBodyText(page, OUR_STORY_BODY_TEXT);
    await saveDraft(page);
    await publishViaMoreActions(page);
  },

  // Relies on navigationItemsSaved (About and Contact in the menu) and
  // navigationAboutChildAdded (Our story published under About) having
  // already run earlier in this same run. About has a live child page now,
  // so it renders as a dropdown toggle instead of a plain link -- clicking
  // it opens the dropdown rather than navigating away.
  async navigationDropdownLive(page) {
    await login(page);
    await page.goto(`${BASE_URL}/en/`);
    await page.waitForLoadState("networkidle");
    await page.getByRole("button", { name: "About" }).click();
  },

  // Relies on navigationItemsSaved having already saved the About and
  // Contact menu items -- unlike the earlier add/save steps, the editor now
  // loads them straight from the database, so this step only needs to
  // reorder and save, not re-add them. Moves Contact (menu item 2) above
  // About using the same fixed InlinePanel section id fillTitleBlockText
  // already relies on elsewhere in this file.
  async navigationReorderSaved(page) {
    await login(page);
    await openMainMenu(page);
    await page
      .locator("#inline_child_menu_items-1-panel-section")
      .getByRole("button", { name: "Move up" })
      .click();
    await saveMainMenu(page);
  },

  async footerFlatMenuEmpty(page) {
    await login(page);
    await openAddFlatMenu(page);
  },

  async footerFlatMenuFilled(page) {
    await login(page);
    await openAddFlatMenu(page);
    await fillFlatMenuDetails(page, {
      title: FOOTER_COLUMN1_TITLE,
      handle: "Footer - Column 1",
      heading: FOOTER_COLUMN1_HEADING,
    });
  },

  async footerInternalItemAdded(page) {
    await login(page);
    await openAddFlatMenu(page);
    await fillFlatMenuDetails(page, {
      title: FOOTER_COLUMN1_TITLE,
      handle: "Footer - Column 1",
      heading: FOOTER_COLUMN1_HEADING,
    });
    await addMainMenuItem(page, "About");
  },

  async footerExternalItemAdded(page) {
    await login(page);
    await openAddFlatMenu(page);
    await fillFlatMenuDetails(page, {
      title: FOOTER_COLUMN1_TITLE,
      handle: "Footer - Column 1",
      heading: FOOTER_COLUMN1_HEADING,
    });
    await addMainMenuItem(page, "About");
    await addCustomUrlMenuItem(page, FOOTER_EXTERNAL_URL, FOOTER_EXTERNAL_LINK_TEXT);
  },

  async footerColumn1Saved(page) {
    await login(page);
    await openAddFlatMenu(page);
    await fillFlatMenuDetails(page, {
      title: FOOTER_COLUMN1_TITLE,
      handle: "Footer - Column 1",
      heading: FOOTER_COLUMN1_HEADING,
    });
    await addMainMenuItem(page, "About");
    await addCustomUrlMenuItem(page, FOOTER_EXTERNAL_URL, FOOTER_EXTERNAL_LINK_TEXT);
    await saveFlatMenu(page);
  },

  // The tutorial page only walks Column 1 step by step and tells the reader
  // to "repeat" for other columns -- but the screenshot embedded after that
  // instruction needs to actually show a second, differently-named column
  // to prove columns are independent, not just describe it. This step
  // creates that second column itself (relying on footerColumn1Saved having
  // already saved Column 1 earlier in this same run) before capturing the
  // public site, the same "set up state a numbered step doesn't walk, but
  // the final screenshot needs" pattern as firstPagesHomePublished relying
  // on hideUnrelatedRootPages.
  async footerLive(page) {
    await login(page);
    await openAddFlatMenu(page);
    await fillFlatMenuDetails(page, {
      title: FOOTER_COLUMN2_TITLE,
      handle: "Footer - Column 2",
      heading: FOOTER_COLUMN2_HEADING,
    });
    await addMainMenuItem(page, "Contact");
    await saveFlatMenu(page);
    await page.goto(`${BASE_URL}/en/`);
    await page.waitForLoadState("networkidle");
  },

  // Languages & translations (tutorial 5). The first three steps view the
  // public site the way a signed-out visitor would, deliberately without
  // calling login() at all: language_dropdown.html is only included from
  // header_desktop.html's `{% else %}` branch, i.e. only when
  // request.user.is_authenticated is False -- found live, since every
  // earlier "public site" screenshot in this suite calls login() first and
  // none of them show a language switcher. No explicit logout step is
  // needed either: browser.newPage() opens a new, isolated browser context
  // with no cookies, so a step simply not calling login() is already
  // signed out.
  async languagesSwitcherOpen(page) {
    await page.goto(`${BASE_URL}/en/`);
    await page.waitForLoadState("networkidle");
    // The Django Debug Toolbar's closed handle sits directly over the
    // language toggle button at this viewport size, and physically
    // intercepts the click -- prepareForCapture() (below) only hides it
    // right before the screenshot is taken, too late for a click during the
    // step itself. Found live: the click hung retrying for 30s against
    // "<div id="djDebugRoot"> intercepts pointer events" until this was
    // added.
    await prepareForCapture(page);
    await page.getByRole("button", { name: "Toggle language" }).click();
  },

  async languagesMaoriHomeEmpty(page) {
    await page.goto(`${BASE_URL}/en/`);
    await page.waitForLoadState("networkidle");
    await prepareForCapture(page);
    await page.getByRole("button", { name: "Toggle language" }).click();
    await page.getByRole("banner").getByRole("link", { name: "Te Reo Māori" }).click();
    await page.waitForLoadState("networkidle");
  },

  async languagesPagesRoot(page) {
    await login(page);
    await page.goto(`${BASE_URL}/cms/pages/1/`);
    await page.waitForLoadState("networkidle");
  },

  async languagesMaoriAboutChooser(page) {
    await login(page);
    const maoriHomeId = await getMaoriHomePageId(page);
    await openAddChildPage(page, maoriHomeId);
  },

  async languagesMaoriAboutContentSlug(page) {
    await login(page);
    const maoriHomeId = await getMaoriHomePageId(page);
    await createContentPage(page, maoriHomeId, MAORI_ABOUT_TITLE);
    await insertBodyBlock(page, "Paragraph block");
    await fillBodyText(page, MAORI_ABOUT_BODY);
    await setPageSlug(page, MAORI_ABOUT_SLUG);
  },

  // Rebuilds the same page from scratch rather than continuing from
  // languagesMaoriAboutContentSlug's state -- each capture step gets its own
  // fresh, isolated browser context (no shared cookies, and this page was
  // never saved by the previous step), the same reason footerLive above
  // rebuilds its own flat menu instead of reusing footerColumn1Saved's.
  async languagesMaoriAboutPublished(page) {
    await login(page);
    const maoriHomeId = await getMaoriHomePageId(page);
    await createContentPage(page, maoriHomeId, MAORI_ABOUT_TITLE);
    await insertBodyBlock(page, "Paragraph block");
    await fillBodyText(page, MAORI_ABOUT_BODY);
    await setPageSlug(page, MAORI_ABOUT_SLUG);
    await publishViaMoreActions(page);
  },

  // Relies on languagesMaoriAboutPublished (the manifest entry just before
  // this one) having already published the Māori About page at the same
  // slug as the English one earlier in this same run.
  async languagesSwitchRoundTrip(page) {
    await page.goto(`${BASE_URL}/en/about/`);
    await page.waitForLoadState("networkidle");
    await prepareForCapture(page);
    await page.getByRole("button", { name: "Toggle language" }).click();
    await page.getByRole("banner").getByRole("link", { name: "Te Reo Māori" }).click();
    await page.waitForLoadState("networkidle");
  },

  async membershipsOptionFormEmpty(page) {
    await login(page);
    await openMembershipOptionAdd(page);
  },

  async membershipsOptionSaved(page) {
    await login(page);
    await openMembershipOptionAdd(page);
    await fillMembershipOptionForm(page);
    await saveAdminForm(page);
  },

  // Relies on membershipsOptionSaved (just before this one) having already
  // created the Standard membership option earlier in this same run.
  async membershipsSignupForm(page) {
    await login(page);
    await openApplyIndividual(page);
  },

  // Clears Mailpit right before submitting, so the two emails this creates
  // (the staff notification and the member's own invoice email) are the
  // only messages membershipsStaffNotification finds later in this run --
  // not leftovers from any earlier manual testing or partial re-run.
  async membershipsSignupSubmitted(page) {
    await login(page);
    await openApplyIndividual(page);
    await selectFirstMembershipOption(page);
    await clearMailpit();
    await registerMembership(page);
  },

  // Relies on membershipsSignupSubmitted (just before this one) having
  // already created the pending application earlier in this same run.
  async membershipsApprovalPending(page) {
    await login(page);
    await openFirstIndividualMembership(page);
  },

  async membershipsApprovalApproved(page) {
    await login(page);
    await openFirstIndividualMembership(page);
    await approveViaTodayNow(page);
    await saveAdminFormContinueEditing(page);
  },

  // Relies on membershipsSignupSubmitted having already cleared Mailpit and
  // triggered exactly two emails earlier in this same run -- this step only
  // views the result, it doesn't send anything itself.
  //
  // Screenshots just the rendered email itself (the #preview-html iframe's
  // real content), not the surrounding Mailpit inbox/tabs/sidebar chrome --
  // a client reader only ever needs to know what the *email* looks like, and
  // Mailpit's own UI (a local-dev-only tool that doesn't exist on their live
  // site) would otherwise be the most visually prominent thing in the image.
  // Returning true tells main() this step already wrote its own screenshot,
  // skipping the usual whole-viewport capture.
  //
  // A plain `locator.screenshot()` on the iframe (tried first) produced two
  // visible problems: a 1-2px dark line along the very top edge, and a large
  // blank gap at the bottom. Both come from the same cause -- the iframe
  // element's own box is a fixed 919px tall regardless of the email's actual
  // length (Mailpit/MJML fill it for background-colour consistency), so an
  // automatic element screenshot clips to that fixed box: its top edge lands
  // exactly on the boundary with Mailpit's tab bar above it (a fractional
  // clip coordinate rounds the wrong way and grabs a sliver of the tab bar's
  // dark border), and its bottom extends ~80px past the email's real last
  // line of text into empty filler space. Taking an explicit `page.screenshot`
  // with a manually computed `clip` fixes both: starting 2px below the
  // iframe's own top (skips the tab-bar sliver) and ending just below the
  // real content's lowest text (found via `getIframeContentBottom`, not the
  // iframe's own height) plus a little breathing room.
  //
  // This needs a taller viewport than the suite's usual 1280x800 -- the
  // clip region this produces is taller than 800px, and Chromium silently
  // truncates a `clip` that extends past the page's current viewport rather
  // than rendering past it. Only this page instance's viewport changes
  // (each capture step gets its own fresh page in main()'s loop), so this
  // doesn't affect any other screenshot's fixed-viewport determinism.
  async membershipsStaffNotification(page, outPath) {
    await page.setViewportSize({ width: VIEWPORT.width, height: 1600 });
    const messageId = await getMailpitMessageIdByFrom("webmaster@localhost");
    await page.goto(`${MAILPIT_ORIGIN}/view/${messageId}`);
    await page.waitForLoadState("networkidle");
    const box = await page.locator("#preview-html").boundingBox();
    const contentBottom = await getIframeContentBottom(page, "#preview-html");
    const TOP_INSET = 2;
    const BOTTOM_PADDING = 24;
    await page.screenshot({
      path: outPath,
      clip: {
        x: box.x,
        y: box.y + TOP_INSET,
        width: box.width,
        height: Math.min(contentBottom - TOP_INSET + BOTTOM_PADDING, box.height - TOP_INSET),
      },
    });
    return true;
  },
};

async function main() {
  if (!ADMIN_EMAIL || !ADMIN_PASSWORD) {
    console.error(
      "Could not read SAMPLE_DATA_ADMIN_EMAIL/SAMPLE_DATA_ADMIN_PASSWORD from .envs/.local/django.ini",
    );
    process.exitCode = 1;
    return;
  }

  const manifest = JSON.parse(fs.readFileSync(MANIFEST_PATH, "utf8"));
  const browser = await chromium.launch();
  let failures = 0;

  for (const entry of manifest) {
    const stepFn = steps[entry.step];
    if (!stepFn) {
      console.error(`No capture step named "${entry.step}" (manifest entry "${entry.id}")`);
      failures += 1;
      continue;
    }

    const page = await browser.newPage({ viewport: VIEWPORT, deviceScaleFactor: DEVICE_SCALE_FACTOR });
    try {
      await proxyMinioMedia(page);
      const outPath = path.join(IMAGES_ROOT, entry.file);
      fs.mkdirSync(path.dirname(outPath), { recursive: true });
      // A step normally just sets up the page and lets the default
      // whole-viewport screenshot below capture it. A step can instead take
      // its own narrower screenshot (e.g. a single element rather than the
      // whole page) and return true to signal it's already written outPath
      // itself, skipping the default capture.
      const capturedItself = await stepFn(page, outPath);
      await prepareForCapture(page);
      if (!capturedItself) {
        await page.screenshot({ path: outPath });
      }
      console.log(`Wrote ${entry.file}`);
    } catch (err) {
      console.error(`Failed to capture "${entry.id}": ${err.message}`);
      failures += 1;
    } finally {
      await page.close();
    }
  }

  await browser.close();

  if (failures > 0) {
    console.error(`${failures} screenshot(s) failed.`);
    process.exitCode = 1;
  } else {
    console.log(`Done. ${manifest.length} screenshot(s) written to ${IMAGES_ROOT}.`);
  }
}

main();
