// Playwright helpers used by two or more tutorial step modules
// (docs/screenshots/steps/*.mjs). A helper used by only one tutorial lives
// in that tutorial's own step file instead -- see that file for anything
// not found here.

import { BASE_URL, MEDIA_LOCALHOST_ORIGIN, MEDIA_CONTAINER_ORIGIN, ADMIN_EMAIL, ADMIN_PASSWORD } from "./config.mjs";

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
//
// The same [data-controller='w-messages'] selector also hides a second,
// unrelated element: Wagtail's own top-of-page save/error toast
// (wagtailadmin/base.html's `<div class="messages" role="status"
// data-controller="w-messages">`, e.g. "Page 'X' has been published.").
// That element happens to reuse the same Stimulus controller name as the
// footer warning above, so this one rule suppresses both -- confirmed by
// inspecting a captured post-save screenshot (branding-theme-08-primary-
// saved.png) and finding no toast visible, even though the step it comes
// from does trigger one. Noted here so a future reader doesn't add a
// second, redundant rule for it.
//
// Wagtail's dashboard also shows an "Upgrade available" banner
// (wagtailadmin/home/upgrade_notification.html, gated on
// WAGTAIL_ENABLE_UPDATE_CHECK), which starts `hidden` and is only unhidden
// by a Stimulus controller (data-controller="w-upgrade") after an async
// fetch to Wagtail's own release-check API -- a real network call whose
// timing/outcome isn't controlled by this suite. Only reachable from the
// two dashboard captures (exampleDashboard, orientationCmsDashboard), but
// hidden here for the same reason as everything else in this function.
//
// Separately, and the biggest single source of byte-different-but-
// visually-identical screenshots found in this suite: Wagtail's admin
// sidebar is client-side (React) rendered and re-mounts on every page
// load, including the "Help" nav item's unread-count badge -- its mount
// animation lands at a different frame depending on real wall-clock
// timing, producing a few thousand sub-pixel antialiasing differences
// confined to that one small corner of the viewport (confirmed directly:
// loading the same admin page twice in a row produced a nonzero pixel
// diff bounded to (42,1180)-(106,1246); adding the blanket
// transition/animation kill below made the same two loads byte-
// identical). Rather than chase this one element, every element's CSS
// transitions and animations are disabled during capture -- the general
// form of the "wait for the real end state, don't race it" fix bullet 12
// established for scroll-behavior, applied suite-wide so a later UI
// change with its own transition doesn't reopen the same class of bug.
//
// One more real, measured cause of the same byte-different-but-visually-
// identical problem, tied to whatever element a step happened to leave
// focused rather than to any CSS transition: a field with autofocus from
// the page itself (found in eventsLocationFormEmpty -- Django admin's own
// add-form autofocus) shows up as a present/absent focus ring depending
// on whether the browser had painted it yet when the screenshot was
// taken (confirmed by a double-run diff bounded to exactly that field's
// outline; gone once this blur was added). No step in this suite is
// actually about showing a focus ring, so the fix is the same "remove
// the nondeterministic chrome" pattern applied one level higher: blur
// whatever's focused right before every capture, in every frame, for the
// same iframe-preview reason bullet 10 already established.
//
// See docs-conventions.md bullet 27 for the full write-up of how the CSS
// transition/animation kill and the focus blur were measured.
export async function prepareForCapture(page) {
  for (const frame of page.frames()) {
    await frame
      .addStyleTag({
        content:
          "#djDebugRoot { display: none !important; } " +
          "[data-controller='w-messages'] { display: none !important; } " +
          "[data-controller='w-upgrade'] { display: none !important; } " +
          "*, *::before, *::after { transition: none !important; animation: none !important; }",
      })
      .catch(() => {});
    await frame.evaluate(() => document.activeElement?.blur()).catch(() => {});
  }
  await prepareForumCapture(page);
}

// Discourse (the forum, T19) carries its own per-account, history-dependent
// chrome that AMS's own #djDebugRoot-style hiding doesn't touch: an unread-
// notification bell badge, an unread dot next to "Topics" in the sidebar, a
// "New (N)" count in the top tab strip, and a personalised "Welcome back,
// <username>!"/"Welcome, <username>!" banner that differs depending on
// whether this SSO account has ever signed in to the forum before. None of
// these are reset by seed.sh -- Discourse has its own database, entirely
// separate from Django's, and seed.sh only flushes Django's. Left alone, a
// screenshot's exact pixels would depend on how many times *any* previous
// pipeline run (on this machine, potentially over the project's whole
// lifetime) happened to sign this account into the forum, not just on
// today's seeded state -- the same "remove the nondeterministic chrome
// element" fix already used for #djDebugRoot above, applied to Discourse's
// own volatile elements instead. Harmless no-op on every non-Discourse page,
// since none of these selectors exist there.
export async function prepareForumCapture(page) {
  await page
    .evaluate(() => {
      document
        .querySelectorAll(
          ".badge-notification.unread-notifications, .sidebar-section-link-suffix.icon.unread, .welcome-banner__title",
        )
        .forEach((el) => el.remove());
      document
        .querySelectorAll("#navigation-bar .nav-item_new a, #navigation-bar .nav-item_unread a")
        .forEach((a) => {
          a.textContent = a.textContent.replace(/\(\d+\)/, "").trim();
        });
    })
    .catch(() => {});
}

// Uploaded media (images, documents) gets a URL under
// DJANGO_MEDIA_PUBLIC_CUSTOM_DOMAIN=localhost:9000/..., which is correct for
// a browser running on the host machine, but this suite's browser runs
// inside the `node` container, where "localhost" means the node container
// itself -- nothing listens on port 9000 there, only on the host and inside
// the `minio` container. Without this, any page showing a real uploaded
// image (e.g. branding-theme's logo) would capture a broken-image icon
// instead. Reroute those specific requests to `minio`, the docker-network
// hostname the `node` container can actually reach.
export async function proxyMinioMedia(page) {
  await page.route(`${MEDIA_LOCALHOST_ORIGIN}/**`, async (route) => {
    const url = new URL(route.request().url());
    const target = `${MEDIA_CONTAINER_ORIGIN}${url.pathname}${url.search}`;
    const response = await route.fetch({ url: target });
    await route.fulfill({ response });
  });
}

export async function loginAs(page, email, password) {
  await page.goto(`${BASE_URL}/en/accounts/login/`);
  await page.fill("#id_login", email);
  await page.fill("#id_password", password);
  await page.click("button[type=submit], input[type=submit]");
  await page.waitForLoadState("networkidle");
}

export async function login(page) {
  await loginAs(page, ADMIN_EMAIL, ADMIN_PASSWORD);
}

// Forum tutorial (T19) needs a second signed-in identity mid-step, to show
// what a member *without* an active membership sees -- the admin account
// used everywhere else in this suite can't demonstrate that, since
// user_has_active_membership() (docs-conventions.md bullet 21) returns True
// for any superuser regardless of its own membership rows. Confirms sign-out
// actually happened by waiting for the Sign In link to reappear, rather than
// just clicking and moving on -- allauth's logout is a confirm-then-POST
// flow, not a single click.
export async function logout(page) {
  await page.goto(`${BASE_URL}/en/accounts/logout/`);
  await page.getByRole("button", { name: "Sign Out" }).click();
  await page.waitForLoadState("networkidle");
}

// The English home page's ID depends on AMS_ENABLED_LANGUAGES's order (see
// docs-conventions.md's "Screenshot content depends on AMS_ENABLED_LANGUAGES"
// note) -- setup_cms creates one HomePage per configured language, in that
// order, so which numeric page ID ends up English varies with the env var.
// Resolved once per run by reading the page explorer, rather than
// hard-coding a page ID that would silently point at the wrong (Māori) home
// page in a differently-configured environment.
let englishHomePageId;
export async function getEnglishHomePageId(page) {
  if (englishHomePageId) return englishHomePageId;
  await page.goto(`${BASE_URL}/cms/pages/1/`);
  await page.waitForLoadState("networkidle");
  const englishRow = page.getByRole("row").filter({ hasText: "English" });
  const homeLink = englishRow.getByRole("link", { name: "Home", exact: true });
  const href = await homeLink.getAttribute("href");
  englishHomePageId = href.match(/\/pages\/(\d+)\//)[1];
  return englishHomePageId;
}

// Languages & translations (tutorial 5) needs the Te Reo Māori Home page's
// ID, the same way getEnglishHomePageId() needs the English one -- resolved
// at runtime rather than hard-coded, for the same reason (it depends on
// AMS_ENABLED_LANGUAGES's order in this environment).
let maoriHomePageId;
export async function getMaoriHomePageId(page) {
  if (maoriHomePageId) return maoriHomePageId;
  await page.goto(`${BASE_URL}/cms/pages/1/`);
  await page.waitForLoadState("networkidle");
  const maoriRow = page.getByRole("row").filter({ hasText: "Māori" });
  const homeLink = maoriRow.getByRole("link", { name: "Home", exact: true });
  const href = await homeLink.getAttribute("href");
  maoriHomePageId = href.match(/\/pages\/(\d+)\//)[1];
  return maoriHomePageId;
}

export async function openAddChildPage(page, parentId) {
  await page.goto(`${BASE_URL}/cms/pages/${parentId}/add_subpage/`);
  await page.waitForLoadState("networkidle");
}

// Starts a new Content page under parentId and fills in its title. Wagtail
// assigns the new page a real ID and switches the URL from .../add/... to
// .../<id>/edit/ as soon as the first body block is inserted (observed
// directly, not assumed) -- callers read that ID back off page.url() after
// inserting a block, rather than guessing it.
export async function createContentPage(page, parentId, title) {
  await openAddChildPage(page, parentId);
  await page.getByRole("link", { name: "Content page", exact: true }).click();
  await page.waitForLoadState("networkidle");
  await page.getByRole("textbox", { name: "Title*" }).fill(title);
}

// Adds a content-page child of an existing ContentPage (About), unlike
// createContentPage's use under Home. ContentPage.subpage_types only
// allows further ContentPage children (ams/cms/models/pages.py), so with
// exactly one allowed type Wagtail skips the page-type chooser and opens
// the add form directly -- confirmed live, not assumed, since it differs
// from createContentPage's chooser-then-click-"Content page" flow under
// Home, which allows more than one child type.
export async function createChildContentPage(page, parentId, title) {
  await openAddChildPage(page, parentId);
  await page.getByRole("textbox", { name: "Title*" }).fill(title);
}

// Uses the *last* "Insert a block" button, not the first, so this works both
// to start an empty Body (only one such button exists, first === last) and
// to append a further block after one already inserted (e.g. a tagline
// after a Title block) -- the first button in that second case would insert
// *before* the existing block instead of after it.
export async function insertBodyBlock(page, blockName) {
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
export async function fillBodyText(page, text) {
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
export async function fillTitleBlockText(page, text) {
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
export async function setPageSlug(page, slug) {
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

export async function saveDraft(page) {
  await page.getByRole("button", { name: "Save draft" }).click();
  await page.waitForLoadState("networkidle");
}

export async function publishViaMoreActions(page) {
  await page.getByRole("button", { name: "More actions" }).click();
  await page.getByRole("button", { name: "Publish" }).click();
  await page.waitForLoadState("networkidle");
}

export function pageIdFromEditUrl(page) {
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
export async function scrollIntoViewInstantly(locator) {
  await locator.evaluate((el) => el.scrollIntoView({ block: "center", behavior: "instant" }));
}

// Scoped to "Save", not "Save and add another"/"Save and continue editing" --
// Django admin's add/change forms always offer all three.
// .first() matters for a ModelAdmin with save_on_top = True (EventAdmin,
// found in T20) -- Django then renders the whole submit row twice (top and
// bottom of the form), so an unscoped locator resolves to two identically-
// named buttons and Playwright's strict mode rejects the click. Harmless on
// every earlier admin form this suite uses, none of which set save_on_top,
// where .first() is just the only match.
export async function saveAdminForm(page) {
  await page.getByRole("button", { name: "Save", exact: true }).first().click();
  await page.waitForLoadState("networkidle");
}

// "Save and continue editing" (not "Save") deliberately, so the screenshot
// right after can show the same record's Status field having flipped from
// Pending to Active in place, rather than navigating away to prove it.
// .first() for the same save_on_top reason as saveAdminForm above.
export async function saveAdminFormContinueEditing(page) {
  await page.getByRole("button", { name: "Save and continue editing" }).first().click();
  await page.waitForLoadState("networkidle");
}
