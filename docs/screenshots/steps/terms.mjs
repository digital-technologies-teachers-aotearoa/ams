// Terms & policies (feature reference, no tutorial). MUST be the last
// tutorial-derived entries in manifest.json, before the marketing set --
// termsVersionsList activates a Term Version that's already enforceable
// (date_active <= now), and from that point on login() itself redirects
// any account without a recorded acceptance to /terms/accept/ instead of
// wherever it would otherwise land (e.g. the account page
// orientationYourAccount, in orientation.mjs, already captured much
// earlier in this same run -- unaffected only because it ran first).
// Confirmed live: only login()'s own redirect target and the forum are
// gated (ams/users/views.py's TermsRequiredMixin, ams/forum/views.py's
// terms_required) -- CMS/Django admin URLs are never gated, so every step
// below can keep using login() + an explicit goto() freely regardless of
// activation order; the one thing activation genuinely breaks for a step
// running afterward is relying on login() alone to land on the account
// page, which no other tutorial's steps do except orientation.mjs's
// (already captured before this file runs).

import { BASE_URL } from "../shared/config.mjs";
import { login } from "../shared/browser-helpers.mjs";

const TERM_KEY = "privacy-policy";
const TERM_NAME = "Privacy Policy";
const TERM_VERSION_LABEL = "1.0";
const TERM_VERSION_CONTENT =
  "We collect your name and email address to manage your membership, and never share them with third parties without your consent.";

async function createTerm(page) {
  await page.goto(`${BASE_URL}/cms/snippets/terms/term/add/`);
  await page.waitForLoadState("networkidle");
  await page.locator("#id_key").fill(TERM_KEY);
  await page.locator("#id_name_en").fill(TERM_NAME);
  await page.getByRole("button", { name: "Save", exact: true }).click();
  await page.waitForLoadState("networkidle");
}

async function chooseTerm(page) {
  await page.getByRole("button", { name: "Choose Term" }).click();
  await page.getByRole("link", { name: TERM_NAME, exact: true }).click();
}

// The Content field is a Draftail-backed RichTextField, same as StreamField
// body blocks, but there's no "Body" region here to scope
// browser-helpers.mjs's fillBodyText against -- a snippet form's translated
// FieldPanel instead wraps each language's editor in its own
// #panel-child-content-child-<field>-wrapper (found live, not assumed).
// Same discipline as fillBodyText otherwise: real keystrokes
// (pressSequentially, not fill()) and a wait for the hidden sync input
// (#id_<field>) to actually contain the typed text, not a fixed pause.
async function fillSnippetRichText(page, fieldName, text) {
  const box = page
    .locator(`#panel-child-content-child-${fieldName}-wrapper`)
    .getByRole("textbox");
  await box.click();
  await box.pressSequentially(text);
  await page.waitForFunction(
    ({ id, expected }) => document.querySelector(`#${id}`)?.value?.includes(expected),
    { id: `id_${fieldName}`, expected: text },
    { timeout: 5000 },
  );
}

// AdminDateTimeInput expects a single "YYYY-MM-DD HH:MM" field (unlike
// events.mjs's split date/time sessions-N-start_0/_1 pair) -- built from
// local date parts, not toISOString() (UTC), same reasoning as events.mjs's
// futureDateISO. A few minutes in the past, not exactly "now", so the
// version is already enforceable (date_active <= now) by the time this
// step's own save request reaches the server, without racing the clock.
// Known-unstable image, same class as docs-conventions.md's bullet 26 list:
// the Date active column (termsVersionsList below) shows this down to the
// minute, so it never regenerates byte-identical between two runs.
function activeDateTimeLocal() {
  const d = new Date(Date.now() - 5 * 60 * 1000);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

async function fillTermVersionForm(page) {
  await page.goto(`${BASE_URL}/cms/snippets/terms/termversion/add/`);
  await page.waitForLoadState("networkidle");
  await chooseTerm(page);
  await page.locator("#id_version").fill(TERM_VERSION_LABEL);
  await page.locator("#id_date_active").fill(activeDateTimeLocal());
  await fillSnippetRichText(page, "content_en", TERM_VERSION_CONTENT);
  await page.getByRole("checkbox", { name: "Is active" }).check();
}

export const steps = {
  // Creates the one Term this run uses (termsVersionsList, below, reuses it
  // rather than creating a second one -- Term.key is unique) and fills the
  // Add Term Version form referencing it, but never submits -- so this
  // step makes no lasting change for termsVersionsList to conflict with.
  async termsVersionFormFilled(page) {
    await login(page);
    await createTerm(page);
    await fillTermVersionForm(page);
  },

  // Relies on termsVersionFormFilled (just before this one) having already
  // created the one Term this run uses. Fills and saves its own Term
  // Version (not the one termsVersionFormFilled left unsaved) -- active and
  // enforceable from here on, which is what makes termsAcceptInterstitial
  // (the last step in this file) show anything at all. Saving redirects to
  // this same list view, which is what the default whole-page screenshot
  // below actually captures.
  async termsVersionsList(page) {
    await login(page);
    await fillTermVersionForm(page);
    await page.getByRole("button", { name: "Save", exact: true }).click();
    await page.waitForLoadState("networkidle");
  },

  // Relies on termsVersionsList, same as this step's own comment.
  async termsPublicPage(page) {
    await login(page);
    await page.goto(`${BASE_URL}/en/terms/`);
    await page.waitForLoadState("networkidle");
  },

  // Relies on termsVersionsList having activated a currently-enforceable
  // Term Version earlier in this same run -- see this file's top comment
  // for why login() alone is enough to land here now, and why this has to
  // stay the last tutorial-derived entry in manifest.json.
  async termsAcceptInterstitial(page) {
    await login(page);
  },
};
