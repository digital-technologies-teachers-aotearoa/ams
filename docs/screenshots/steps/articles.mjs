// Articles (feature reference, no tutorial -- see cms.md's "not covered by
// the tutorial series" note) capture steps create real pages, so like
// first-pages.mjs, they only produce correct screenshots when run in
// manifest.json's declared order against a just-seeded site, in one
// docs:screenshots invocation -- see docs-conventions.md's "Ordering for
// capture steps that change site state" bullet. Must also run after every
// other Home-page-touching tutorial (first-pages, at minimum) so the
// Recent Articles block is added on top of that existing Title/Lead
// paragraph content, not a blank Body.

import path from "node:path";
import { BASE_URL, SCREENSHOTS_ROOT } from "../shared/config.mjs";
import {
  login,
  getEnglishHomePageId,
  openAddChildPage,
  insertBodyBlock,
  fillBodyText,
  saveDraft,
  publishViaMoreActions,
  pageIdFromEditUrl,
  scrollIntoViewInstantly,
} from "../shared/browser-helpers.mjs";

const ARTICLES_INDEX_TITLE = "Articles";
const ARTICLE_TITLE = "New workshops for Term 3";
const ARTICLE_AUTHOR = "Priya Patel";
const ARTICLE_SUMMARY =
  "A quick look at what's new this term, including two workshops and updated resources for your classroom.";
const ARTICLE_BODY_TEXT =
  "This term we're running two professional development workshops for members, plus new curriculum resources in the Year 9 and Year 10 categories.";
const ARTICLE_COVER_TITLE = "New workshops for Term 3 cover image";
const ARTICLE_COVER_FIXTURE = path.join(SCREENSHOTS_ROOT, "fixtures", "demo-article-cover.png");

let articlePageId;

async function openHomeEdit(page) {
  const homeId = await getEnglishHomePageId(page);
  await page.goto(`${BASE_URL}/cms/pages/${homeId}/edit/`);
  await page.waitForLoadState("networkidle");
}

// Same Upload-tab-then-file pattern as branding-theme.mjs's
// openLogoUploadTab/uploadDemoLogo, scoped to the cover_image field instead
// of association_logo -- kept local rather than generalised into
// browser-helpers.mjs, matching that file's own stated rule that a helper
// used by only one tutorial belongs in that tutorial's own step file.
async function uploadCoverImage(page) {
  await page.locator("#id_cover_image-chooser [data-chooser-action-choose]").click();
  const modal = page.locator('[role="dialog"][aria-hidden="false"]');
  await modal.getByRole("tab", { name: "Search" }).waitFor({ state: "visible" });
  await modal.getByRole("tab", { name: "Upload" }).click();
  await modal.locator("#id_image-chooser-upload-title").waitFor({ state: "visible" });
  await modal.locator("#id_image-chooser-upload-title").fill(ARTICLE_COVER_TITLE);
  await modal.locator("#id_image-chooser-upload-file").setInputFiles(ARTICLE_COVER_FIXTURE);
  await modal.getByRole("button", { name: "Upload" }).click();

  // Defensive, not expected on a fresh seed.sh run: only guards against a
  // re-run against a not-yet-reseeded database uploading this fixture twice
  // -- the same duplicate-image interstitial branding-theme.mjs's
  // uploadDemoLogo already guards against, for the same reason.
  const useNewImage = modal.getByRole("link", { name: "Use new image" });
  const isDuplicate = await useNewImage
    .waitFor({ state: "visible", timeout: 3000 })
    .then(() => true)
    .catch(() => false);
  if (isDuplicate) {
    await useNewImage.click();
  }

  await page.waitForFunction(
    (title) => document.querySelector("#id_cover_image-title")?.textContent.trim() === title,
    ARTICLE_COVER_TITLE,
  );
}

export const steps = {
  // The page-type chooser under Home, showing Articles index page alongside
  // Content page -- proves it's a selectable type without yet creating one.
  async articlesAddIndexChooser(page) {
    await login(page);
    const homeId = await getEnglishHomePageId(page);
    await openAddChildPage(page, homeId);
  },

  // Articles index page has just a Title and an optional Intro (no
  // StreamField), so unlike Home's Title block this can be created and
  // published in one step without the block-clobbering race first-pages.md
  // documents. Publishing redirects to the parent's (Home's) explorer, the
  // same "confirmation" pattern first-pages.mjs's firstPagesHomePublished/
  // firstPagesAboutPublished rely on.
  //
  // A gotcha not yet documented elsewhere in this suite, found live: on a
  // brand-new page, the Slug field (Promote tab) only gets auto-populated
  // from the Title once the Title field genuinely blurs *and* an async
  // slug-suggestion request Wagtail fires on that blur has resolved --
  // .fill()-ing the Title alone never triggers it (confirmed: the field
  // stayed empty even after clicking Publish), and clicking straight to
  // More actions/Publish afterward isn't a real enough focus change either.
  // Every other tutorial that creates a page happens to dodge this by
  // clicking into a StreamField block (fillBodyText's real .click()) before
  // ever saving, which incidentally provides both the blur and enough
  // elapsed time -- Articles index page has no Body, so this clicks the
  // Intro field on purpose to get the same effect, and waits for the actual
  // slug value rather than guessing how long the request takes.
  async articlesIndexPublished(page) {
    await login(page);
    const homeId = await getEnglishHomePageId(page);
    await openAddChildPage(page, homeId);
    await page.getByRole("link", { name: "Articles index page", exact: true }).click();
    await page.waitForLoadState("networkidle");
    await page.getByRole("textbox", { name: "Title*" }).fill(ARTICLES_INDEX_TITLE);
    await page.getByRole("region", { name: "Intro" }).getByRole("textbox").click();
    await page.waitForFunction(() => document.querySelector("#id_slug")?.value, {
      timeout: 5000,
    });
    await publishViaMoreActions(page);
  },

  // Relies on articlesIndexPublished (just before this one) having already
  // published the one and only Articles index page earlier in this same
  // run -- the sidebar "Articles" listing's "Add article page" link
  // (/cms/article_pages/choose_parent/) auto-resolves straight to the add
  // form when exactly one valid parent exists, skipping its own chooser
  // step. Confirmed live: with zero Articles index pages it shows a parent
  // chooser instead, and the "Create a new article page" button stays
  // disabled until one is picked.
  async articlesArticleFormEmpty(page) {
    await login(page);
    await page.goto(`${BASE_URL}/cms/article_pages/choose_parent/?locale=en`);
    await page.waitForLoadState("networkidle");
  },

  // Relies on articlesIndexPublished, same as articlesArticleFormEmpty above.
  async articlesArticleFormFilled(page) {
    await login(page);
    await page.goto(`${BASE_URL}/cms/article_pages/choose_parent/?locale=en`);
    await page.waitForLoadState("networkidle");
    await page.getByRole("textbox", { name: "Title*" }).fill(ARTICLE_TITLE);
    await page.getByRole("textbox", { name: "Author" }).fill(ARTICLE_AUTHOR);
    await page.getByRole("textbox", { name: "Summary*" }).fill(ARTICLE_SUMMARY);
    await uploadCoverImage(page);
    // Publication date is left at its default (now), so the article is
    // immediately live once published -- no scheduling step needed for
    // this capture. See docs-conventions.md's known-unstable-images bullet:
    // the date this renders as on the live pages (articles-06/07 below)
    // only stays byte-stable within the same calendar day.
    await insertBodyBlock(page, "Paragraph block");
    await fillBodyText(page, ARTICLE_BODY_TEXT);
    // Belt-and-braces: fillBodyText's own click() on the Body field already
    // blurs Title and gives the async slug-suggestion request time to
    // resolve (see articlesIndexPublished's comment for the underlying
    // gotcha), but this waits for the actual value rather than assuming.
    await page.waitForFunction(() => document.querySelector("#id_slug")?.value, {
      timeout: 5000,
    });
    await saveDraft(page);
    articlePageId = pageIdFromEditUrl(page);
    // Same floating Save draft/More actions bar overlap as
    // first-pages.mjs's firstPagesAboutContent -- see its own comment.
    await scrollIntoViewInstantly(
      page.getByRole("region", { name: "Body" }).getByRole("textbox").last(),
    );
  },

  // Relies on articlesArticleFormFilled (just before this one) having
  // already created and saved the article as a draft earlier in this same
  // run.
  async articlesArticlePublished(page) {
    await login(page);
    await page.goto(`${BASE_URL}/cms/pages/${articlePageId}/edit/`);
    await page.waitForLoadState("networkidle");
    await publishViaMoreActions(page);
  },

  // Relies on articlesArticlePublished, same as this step's own comment.
  async articlesListingLive(page) {
    await login(page);
    await page.goto(`${BASE_URL}/en/articles/`);
    await page.waitForLoadState("networkidle");
  },

  // Relies on articlesArticlePublished, same as articlesListingLive above.
  // The card's title (cms/partials/article_card.html) is a plain <h5>, not
  // a link -- only its "Read more" button is, styled as a stretched-link
  // covering the whole card -- so that's the accessible name to click,
  // not the article's own title text.
  async articlesDetailLive(page) {
    await login(page);
    await page.goto(`${BASE_URL}/en/articles/`);
    await page.waitForLoadState("networkidle");
    await page.getByRole("link", { name: "Read more" }).click();
    await page.waitForLoadState("networkidle");
  },

  // Recent Articles is Home-page-only (ams/cms/blocks/layout_stream_blocks.py)
  // -- added on top of the Title/Lead paragraph blocks first-pages.mjs's
  // steps already saved to Home's Body earlier in this same run, not a
  // blank page. Its one field, article_count, defaults to "3 articles", so
  // no interaction with it is needed to show a realistic, working default.
  async articlesRecentBlockAdded(page) {
    await login(page);
    await openHomeEdit(page);
    await insertBodyBlock(page, "Recent Articles");
    await saveDraft(page);
    await scrollIntoViewInstantly(page.getByRole("button", { name: "Insert a block" }).last());
  },

  // Relies on articlesRecentBlockAdded (just before this one) having
  // already saved the block as a draft earlier in this same run, and on
  // articlesArticlePublished having already published the one article the
  // block will actually list.
  async articlesRecentBlockLive(page) {
    await login(page);
    await openHomeEdit(page);
    await publishViaMoreActions(page);
    await page.goto(`${BASE_URL}/en/`);
    await page.waitForLoadState("networkidle");
  },
};
