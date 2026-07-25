// Shared constants and environment loading for the screenshot suite. See
// docs/docs/developer/docs-conventions.md ("How to regenerate screenshots")
// for the seeding prerequisites these values assume.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
export const SCREENSHOTS_ROOT = path.resolve(__dirname, "..");
export const REPO_ROOT = path.resolve(SCREENSHOTS_ROOT, "..", "..");
export const IMAGES_ROOT = path.join(REPO_ROOT, "docs", "docs", "images");
export const MANIFEST_PATH = path.join(SCREENSHOTS_ROOT, "manifest.json");

export const BASE_URL = process.env.DOCS_SCREENSHOTS_BASE_URL ?? "http://localhost:3000";
export const VIEWPORT = { width: 1280, height: 800 };
export const DEVICE_SCALE_FACTOR = 2;

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
export const ADMIN_EMAIL = localEnv.SAMPLE_DATA_ADMIN_EMAIL;
export const ADMIN_PASSWORD = localEnv.SAMPLE_DATA_ADMIN_PASSWORD;
// Forum tutorial (T19) needs the same address AMS itself redirects to for its
// `/forum/` SSO entry point, not a value made up separately -- reads the same
// env var `ams/forum/views.py` reads (`settings.DISCOURSE_REDIRECT_DOMAIN`),
// so this can't drift from what a capture step actually gets redirected to.
export const DISCOURSE_ORIGIN = localEnv.DISCOURSE_REDIRECT_DOMAIN;

export const MAILPIT_ORIGIN = "http://mailpit:8025";

export const MEDIA_LOCALHOST_ORIGIN = "http://localhost:9000";
export const MEDIA_CONTAINER_ORIGIN = "http://minio:9000";

// Same class of problem as MEDIA_LOCALHOST_ORIGIN above, for the forum
// (T19): DISCOURSE_ORIGIN (read from DISCOURSE_REDIRECT_DOMAIN, http://
// localhost with no port -- i.e. port 80) is correct for a browser on the
// host machine, but the `node` container's own "localhost" is the `node`
// container itself, where nothing listens on port 80.
//
// A page.route()-based proxy (the same pattern proxyMinioMedia uses) was
// tried first and rejected after real testing, not by inspection: Discourse's
// SSO flow is a multi-hop redirect chain that crosses back and forth between
// this origin and AMS's own (localhost:3000, already reachable), and two
// separate problems showed up live. First, route.fetch()'s own automatic
// redirect-following resolves each hop's literal (unreachable) Location
// header itself, bypassing page.route() entirely for that hop -- setting
// `maxRedirects: 0` and re-fulfilling each hop by hand avoided that, but
// second, fulfilling a request with content actually fetched from a
// *different* origin (e.g. serving AMS's login page under a URL the browser
// still believes is `http://localhost`) breaks that page's own relative
// asset URLs, which resolve against the URL the browser is on, not the
// origin the content actually came from -- confirmed live by seeing the
// login page render with no CSS, all its static assets 404ing.
//
// The fix that actually works, with none of that complexity: Chromium's own
// `--host-resolver-rules` launch flag, which remaps a hostname:port at the
// browser's network layer itself, before any request is even made -- so
// every request the browser makes to `localhost:80` (the initial navigation,
// every background request Discourse's own Ember app makes back to its own
// origin as it runs, everything) transparently reaches the `discourse`
// container instead, indistinguishably from actually being on that origin.
// No interception, no content fulfillment across origins, so no broken
// asset resolution -- confirmed live, complete with correct CSS/JS loading.
// Set once on the single `chromium.launch()` call in main() (run.mjs),
// covering every step's page for the whole run; harmless for every non-forum
// step, which never requests `localhost:80` at all.
export const CHROMIUM_ARGS = ["--host-resolver-rules=MAP localhost:80 discourse:80"];
