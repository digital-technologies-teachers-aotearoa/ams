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

async function login(page) {
  await page.goto(`${BASE_URL}/en/accounts/login/`);
  await page.fill("#id_login", ADMIN_EMAIL);
  await page.fill("#id_password", ADMIN_PASSWORD);
  await page.click("button[type=submit], input[type=submit]");
  await page.waitForLoadState("networkidle");
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
