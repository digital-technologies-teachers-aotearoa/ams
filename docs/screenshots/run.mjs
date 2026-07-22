#!/usr/bin/env node
// Regenerates every screenshot in manifest.json against a local instance seeded
// with `sample_data`. Run inside the node container: `npm run docs:screenshots`.
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
// every capture.
async function prepareForCapture(page) {
  await page.addStyleTag({ content: "#djDebugRoot { display: none !important; }" });
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

// Capture steps, keyed by the "step" field in manifest.json. Tutorial tasks
// (T13+) add their own steps and manifest entries here as they document
// each screen.
const steps = {
  async exampleLogin(page) {
    await page.goto(`${BASE_URL}/en/accounts/login/`);
    await page.waitForLoadState("networkidle");
    // The site navbar/footer (not the Wagtail admin dashboard, which uses its
    // own "site_name" nickname) is where AssociationSettings.association_*
    // actually renders, so this is the reliable place to sanity-check seeding.
    const bodyText = await page.textContent("body");
    if (!bodyText.includes(DEMO_ORG_NAME)) {
      console.warn(
        `Warning: expected to see the demo organisation name "${DEMO_ORG_NAME}" on the ` +
          "site but didn't. Did you run the AssociationSettings seeding step from " +
          "docs-conventions.md after sample_data?",
      );
    }
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
