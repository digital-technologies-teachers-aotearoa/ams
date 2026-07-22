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
async function prepareForCapture(page) {
  for (const frame of page.frames()) {
    await frame
      .addStyleTag({ content: "#djDebugRoot { display: none !important; }" })
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
      await stepFn(page);
      await prepareForCapture(page);
      const outPath = path.join(IMAGES_ROOT, entry.file);
      fs.mkdirSync(path.dirname(outPath), { recursive: true });
      await page.screenshot({ path: outPath });
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
