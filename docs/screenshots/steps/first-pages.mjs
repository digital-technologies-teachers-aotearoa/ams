// Your first pages (tutorial 3) capture steps create and edit real pages, so
// like branding & theme's steps, they only produce correct screenshots when
// run in manifest.json's declared order against a just-seeded site -- see
// docs-conventions.md's "Ordering for capture steps that change site state"
// bullet.

import { BASE_URL } from "../shared/config.mjs";
import { pageState } from "../shared/shared-state.mjs";
import {
  login,
  getEnglishHomePageId,
  openAddChildPage,
  createContentPage,
  insertBodyBlock,
  fillBodyText,
  fillTitleBlockText,
  saveDraft,
  publishViaMoreActions,
  pageIdFromEditUrl,
  scrollIntoViewInstantly,
} from "../shared/browser-helpers.mjs";

const HOME_TITLE_TEXT = "Welcome to Mathematics Teachers Association";
const HOME_TAGLINE_TEXT =
  "Supporting maths teachers with resources, events, and a community.";
const ABOUT_BODY_TEXT =
  "Mathematics Teachers Association supports maths teachers across the country with resources, events, and a community forum.";
const CONTACT_RECIPIENT_EMAIL = "hello@mathematicsteachers.example";

async function openHomeEdit(page) {
  const homeId = await getEnglishHomePageId(page);
  await page.goto(`${BASE_URL}/cms/pages/${homeId}/edit/`);
  await page.waitForLoadState("networkidle");
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

export const steps = {
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
    pageState.aboutPageId = pageIdFromEditUrl(page);
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
    await page.goto(`${BASE_URL}/cms/pages/${pageState.aboutPageId}/edit/`);
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
    pageState.contactPageId = pageIdFromEditUrl(page);
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
    await page.goto(`${BASE_URL}/cms/pages/${pageState.contactPageId}/edit/`);
    await page.waitForLoadState("networkidle");
    await publishViaMoreActions(page);
    await page.goto(`${BASE_URL}/en/contact/`);
    await page.waitForLoadState("networkidle");
  },
};
