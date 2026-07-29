#!/usr/bin/env node
// Regenerates every screenshot in manifest.json against a local instance seeded
// by seed.sh (an empty skeleton site, not `sample_data`). Run inside the node
// container: `npm run docs:screenshots`.
// See docs/docs/developer/docs-conventions.md ("How to regenerate screenshots")
// for the seeding prerequisites.
//
// This file is the entrypoint only: shared constants live in lib/config.mjs,
// Playwright helpers used by two or more tutorials live in
// lib/browser-helpers.mjs, and each tutorial's own capture steps (plus any
// constants/helpers only it needs) live in steps/<tutorial>.mjs.

import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

import { IMAGES_ROOT, MANIFEST_PATH, VIEWPORT, DEVICE_SCALE_FACTOR, ADMIN_EMAIL, ADMIN_PASSWORD, CHROMIUM_ARGS } from "./shared/config.mjs";
import { prepareForCapture, proxyMinioMedia } from "./shared/browser-helpers.mjs";

import { steps as docsConventionsExamplesSteps } from "./steps/docs-conventions-examples.mjs";
import { steps as orientationSteps } from "./steps/orientation.mjs";
import { steps as brandingThemeSteps } from "./steps/branding-theme.mjs";
import { steps as firstPagesSteps } from "./steps/first-pages.mjs";
import { steps as navigationMenusSteps } from "./steps/navigation-menus.mjs";
import { steps as languagesTranslationsSteps } from "./steps/languages-translations.mjs";
import { steps as membershipsSteps } from "./steps/memberships.mjs";
import { steps as profileFieldsSteps } from "./steps/profile-fields.mjs";
import { steps as forumSteps } from "./steps/forum.mjs";
import { steps as eventsSteps } from "./steps/events.mjs";
import { steps as resourcesSteps } from "./steps/resources.mjs";
import { steps as invitingYourTeamSteps } from "./steps/inviting-your-team.mjs";
import { steps as featuresMarketingSteps } from "./steps/features-marketing.mjs";

// Capture steps, keyed by the "step" field in manifest.json. Tutorial tasks
// (T13+) add their own module to steps/ and list it here as they document
// each screen.
const steps = {
  ...docsConventionsExamplesSteps,
  ...orientationSteps,
  ...brandingThemeSteps,
  ...firstPagesSteps,
  ...navigationMenusSteps,
  ...languagesTranslationsSteps,
  ...membershipsSteps,
  ...profileFieldsSteps,
  ...forumSteps,
  ...eventsSteps,
  ...resourcesSteps,
  ...invitingYourTeamSteps,
  ...featuresMarketingSteps,
};

// Optional argv filter (`node run.mjs [prefix...]`, or `npm run
// docs:screenshots -- <prefix...>`) so working on one tutorial doesn't
// require rewriting and re-diffing every image every time -- restricts
// the run to manifest entries whose `step` or `id` starts with one of the
// given prefixes, e.g. `events` for every `events*` step. No args runs
// the full manifest, unchanged from before this option existed.
//
// Only safe for a tutorial whose steps don't depend on an earlier
// tutorial's state (bullet 8's "state genuinely carries over between
// capture steps" applies here too) -- e.g. `events` is self-contained,
// but `navigation` alone would miss `pageState.aboutPageId`/`contactPageId`
// (lib/shared-state.mjs), which only exist because first-pages.mjs's own
// steps ran first in the same invocation. For anything that depends on
// earlier tutorials, run the full suite.
function filterManifest(manifest, prefixes) {
  if (prefixes.length === 0) return manifest;
  return manifest.filter((entry) =>
    prefixes.some((prefix) => entry.step.startsWith(prefix) || entry.id.startsWith(prefix)),
  );
}

async function main() {
  if (!ADMIN_EMAIL || !ADMIN_PASSWORD) {
    console.error(
      "Could not read SAMPLE_DATA_ADMIN_EMAIL/SAMPLE_DATA_ADMIN_PASSWORD from .envs/.local/django.ini",
    );
    process.exitCode = 1;
    return;
  }

  const prefixes = process.argv.slice(2);
  const fullManifest = JSON.parse(fs.readFileSync(MANIFEST_PATH, "utf8"));
  const manifest = filterManifest(fullManifest, prefixes);
  if (manifest.length === 0) {
    console.error(`No manifest entries matched filter: ${prefixes.join(", ")}`);
    process.exitCode = 1;
    return;
  }
  if (prefixes.length > 0) {
    console.log(`Filtering to ${manifest.length}/${fullManifest.length} manifest entries matching: ${prefixes.join(", ")}`);
  }

  const browser = await chromium.launch({ args: CHROMIUM_ARGS });
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
