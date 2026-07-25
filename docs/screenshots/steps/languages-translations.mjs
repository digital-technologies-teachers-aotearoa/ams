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

import { BASE_URL } from "../shared/config.mjs";
import {
  login,
  prepareForCapture,
  openAddChildPage,
  createContentPage,
  insertBodyBlock,
  fillBodyText,
  setPageSlug,
  publishViaMoreActions,
  getMaoriHomePageId,
} from "../shared/browser-helpers.mjs";

const MAORI_ABOUT_TITLE = "Mō mātou";
const MAORI_ABOUT_BODY = "Nau mai, haere mai ki tō mātou paetukutuku.";
const MAORI_ABOUT_SLUG = "about";

export const steps = {
  async languagesSwitcherOpen(page) {
    await page.goto(`${BASE_URL}/en/`);
    await page.waitForLoadState("networkidle");
    // The Django Debug Toolbar's closed handle sits directly over the
    // language toggle button at this viewport size, and physically
    // intercepts the click -- prepareForCapture() (called from main()'s
    // capture loop) only hides it right before the screenshot is taken, too
    // late for a click during the step itself. Found live: the click hung
    // retrying for 30s against "<div id="djDebugRoot"> intercepts pointer
    // events" until this was added.
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
  // never saved by the previous step), the same reason footerLive
  // (navigation-menus.mjs) rebuilds its own flat menu instead of reusing
  // footerColumn1Saved's.
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
};
