// Branding & theme (tutorial 2) capture steps mutate real site state (the
// association logo, the primary colour) instead of just reading it, so
// unlike the read-only orientation steps, they only produce correct
// screenshots when run in `manifest.json`'s declared order against a
// just-seeded site, in one `docs:screenshots` invocation — see the ordering
// note in docs-conventions.md's "Idempotent capture steps" bullet.

import { BASE_URL, SCREENSHOTS_ROOT } from "../shared/config.mjs";
import { login } from "../shared/browser-helpers.mjs";
import path from "node:path";

const DEMO_ORG_NAME = "Mathematics Teachers Association";
const DEMO_LOGO_TITLE = "Mathematics Teachers Association logo";
const DEMO_LOGO_FIXTURE = path.join(SCREENSHOTS_ROOT, "fixtures", "demo-logo.png");
const THEME_PRIMARY_BRAND = "#7b1fa2";
const THEME_FONT_BRAND = '"Poppins", "Helvetica Neue", sans-serif';

async function openAssociationSettings(page) {
  await page.goto(`${BASE_URL}/cms/settings/cms/associationsettings/`);
  await page.waitForLoadState("networkidle");
}

async function openThemeSettings(page) {
  await page.goto(`${BASE_URL}/cms/settings/cms/themesettings/`);
  await page.waitForLoadState("networkidle");
}

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

export const steps = {
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
};
