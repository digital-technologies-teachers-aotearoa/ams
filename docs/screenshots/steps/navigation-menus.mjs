// Navigation & menus (tutorial 4) builds a Main menu around the About and
// Contact pages "Your first pages" (tutorial 3) already created and
// published, and adds one more child page under About to demonstrate an
// automatic dropdown -- these steps only make sense to run after the
// first-pages.mjs steps earlier in manifest.json's order, the same
// same-run-dependency pattern branding/first-pages steps already rely on.
//
// Footer links (also part of tutorial 4) use Flat menus, a separate
// wagtailmenus model from the Main menu but the same underlying
// InlinePanel machinery for its items -- WAGTAILMENUS_MAIN_MENU_ITEMS_RELATED_NAME
// and WAGTAILMENUS_FLAT_MENU_ITEMS_RELATED_NAME both default to 'menu_items'
// (confirmed in wagtailmenus/conf/defaults.py, not assumed), so
// addMainMenuItem's "Add menu item" / "Choose a page" flow and its
// `inline_child_menu_items-*-panel-section` selector work unmodified for
// flat menus too -- reused directly below rather than duplicated.

import { BASE_URL } from "../shared/config.mjs";
import { pageState } from "../shared/shared-state.mjs";
import {
  login,
  createChildContentPage,
  insertBodyBlock,
  fillBodyText,
  saveDraft,
  publishViaMoreActions,
  scrollIntoViewInstantly,
} from "../shared/browser-helpers.mjs";

const OUR_STORY_BODY_TEXT =
  "Mathematics Teachers Association was founded by volunteer teachers who wanted an easier way to share resources.";
const FOOTER_COLUMN1_TITLE = "Footer column 1";
const FOOTER_COLUMN1_HEADING = "Quick links";
const FOOTER_EXTERNAL_URL = "https://example.org";
const FOOTER_EXTERNAL_LINK_TEXT = "Curriculum resources";
const FOOTER_COLUMN2_TITLE = "Footer column 2";
const FOOTER_COLUMN2_HEADING = "Get in touch";

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

export const steps = {
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
  // for creating and publishing a page. Reuses pageState.aboutPageId, set by
  // firstPagesAboutContent earlier in this same run. Publishing a non-root
  // page lands on its *parent's* page listing (confirmed live: publishing a
  // child of About redirects to About's own listing, the same way
  // publishing About itself redirected to Home's listing in
  // firstPagesAboutPublished) -- no extra navigation needed after
  // publishViaMoreActions for the screenshot to show "Our story" listed
  // under About.
  async navigationAboutChildAdded(page) {
    await login(page);
    await createChildContentPage(page, pageState.aboutPageId, "Our story");
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
  // About using a fixed InlinePanel section id, the same pattern
  // browser-helpers.mjs's fillTitleBlockText relies on elsewhere.
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
};
