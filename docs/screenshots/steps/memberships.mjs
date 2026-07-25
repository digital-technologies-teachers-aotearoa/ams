// Memberships (tutorial 6). Membership options are managed in the Django
// admin, not the CMS -- these steps build on each other in the same way
// branding/first-pages' state-changing steps do: this tutorial's own option
// and application only exist once earlier steps in manifest.json's order
// have created them in this run.

import { BASE_URL, MAILPIT_ORIGIN, VIEWPORT } from "../shared/config.mjs";
import {
  login,
  saveAdminForm,
  saveAdminFormContinueEditing,
  scrollIntoViewInstantly,
} from "../shared/browser-helpers.mjs";

const MEMBERSHIP_OPTION_NAME = "Standard membership";
const MEMBERSHIP_OPTION_DURATION_NUM = "1";
const MEMBERSHIP_OPTION_COST = "40";
const MEMBERSHIP_OPTION_INVOICE_REFERENCE = "MTA Membership";

async function openMembershipOptionAdd(page) {
  await page.goto(`${BASE_URL}/admin/memberships/membershipoption/add/`);
  await page.waitForLoadState("networkidle");
}

// Individual is already the default selection for Type (the first
// MembershipOptionType choice), so this only needs to fill the fields that
// don't already have a usable default.
async function fillMembershipOptionForm(page) {
  await page.getByRole("textbox", { name: "Name:" }).fill(MEMBERSHIP_OPTION_NAME);
  await page.locator("#id_duration_0").fill(MEMBERSHIP_OPTION_DURATION_NUM);
  await page.locator("#id_duration_1").selectOption("Years");
  await page.getByRole("spinbutton", { name: "Cost:" }).fill(MEMBERSHIP_OPTION_COST);
  await page
    .getByRole("textbox", { name: "Invoice Reference:" })
    .fill(MEMBERSHIP_OPTION_INVOICE_REFERENCE);
}

async function openApplyIndividual(page) {
  await page.goto(`${BASE_URL}/en/users/memberships/apply-individual/`);
  await page.waitForLoadState("networkidle");
}

// PricingCardsRadio (ams/templates/utils/crispy_forms/pricing_card.html)
// renders each option as a real <input class="btn-check"> paired with a
// <label class="pricing-card">, Bootstrap's checked-button pattern -- the
// input itself is visually hidden, so clicking/checking it directly always
// resolves to whatever's visually on top at its coordinates (the card's own
// header, or the page's fixed navbar) rather than actually selecting it.
// Clicking the associated <label> instead is what a real visitor's click
// lands on, and toggles the input via the native for= association.
// This tutorial's site only ever has the one membership option this same
// run created earlier, so the first (only) pricing card is always the right
// one -- the same "only one exists" simplification navigation-menus.mjs's
// addMainMenuItem relies on for its own single-button case.
async function selectFirstMembershipOption(page) {
  const label = page.locator("label.pricing-card").first();
  await scrollIntoViewInstantly(label);
  await label.click();
}

async function registerMembership(page) {
  await page.getByRole("button", { name: "Register membership" }).click();
  await page.waitForLoadState("networkidle");
}

// Deletes every message Mailpit is currently holding via its HTTP API, called
// from the script's own Node process (not the browser) -- this doesn't need
// a page open, just a network call from inside the same node container,
// which can already reach every other compose service by name.
async function clearMailpit() {
  await fetch(`${MAILPIT_ORIGIN}/api/v1/messages`, { method: "DELETE" });
}

// Finds the ID of the one message from a given sender address, via Mailpit's
// own HTTP API (not the browser) -- used to open a specific message directly
// by its /view/<id> URL rather than picking through the inbox list on
// screen. Assumes clearMailpit() ran earlier in this same step, so exactly
// the messages a single action produced are present.
async function getMailpitMessageIdByFrom(fromAddress) {
  const res = await fetch(`${MAILPIT_ORIGIN}/api/v1/messages`);
  const data = await res.json();
  const match = data.messages.find((m) => m.From?.Address === fromAddress);
  return match ? match.ID : null;
}

// Finds how far down an iframe's real (non-whitespace) text content extends,
// in the iframe's own local coordinate space. Mailpit's #preview-html iframe
// (the email's rendered HTML) is forced to a fixed height regardless of the
// actual email's length -- MJML-generated emails set html/body to fill their
// container for consistent background colour across email clients, so the
// iframe's own scrollHeight is *not* a usable signal for where the visible
// content actually ends. Walking every text node and taking the lowest one's
// bounding rect finds the real answer regardless of surrounding layout
// wrappers or background-only filler elements.
async function getIframeContentBottom(page, iframeSelector) {
  return await page.evaluate((sel) => {
    const el = document.querySelector(sel);
    const doc = el.contentDocument;
    const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT);
    let node;
    let maxBottom = 0;
    while ((node = walker.nextNode())) {
      if (!node.textContent.trim()) continue;
      const range = doc.createRange();
      range.selectNodeContents(node);
      const rect = range.getBoundingClientRect();
      if (rect.bottom > maxBottom) maxBottom = rect.bottom;
    }
    return maxBottom;
  }, iframeSelector);
}

// This run's only Membership: Individual record, so the single result row's
// own link is always the right one to open -- the same "only one exists"
// simplification selectFirstMembershipOption relies on above.
async function openFirstIndividualMembership(page) {
  await page.goto(`${BASE_URL}/admin/memberships/individualmembership/`);
  await page.waitForLoadState("networkidle");
  await page.getByRole("link", { name: "Admin Account" }).click();
  await page.waitForLoadState("networkidle");
}

// Sets Approved datetime to now via the admin's own "Today"/"Now" quick-fill
// links, scoped to the approved_datetime field row specifically -- Start
// date and Expiry date above it have their own identically-labelled "Today"
// links, so an unscoped page-wide lookup would be ambiguous.
async function approveViaTodayNow(page) {
  const field = page.locator(".field-approved_datetime");
  await field.getByRole("link", { name: "Today" }).click();
  await field.getByRole("link", { name: "Now" }).click();
}

export const steps = {
  async membershipsOptionFormEmpty(page) {
    await login(page);
    await openMembershipOptionAdd(page);
  },

  async membershipsOptionSaved(page) {
    await login(page);
    await openMembershipOptionAdd(page);
    await fillMembershipOptionForm(page);
    await saveAdminForm(page);
  },

  // Relies on membershipsOptionSaved (just before this one) having already
  // created the Standard membership option earlier in this same run.
  async membershipsSignupForm(page) {
    await login(page);
    await openApplyIndividual(page);
  },

  // Clears Mailpit right before submitting, so the two emails this creates
  // (the staff notification and the member's own invoice email) are the
  // only messages membershipsStaffNotification finds later in this run --
  // not leftovers from any earlier manual testing or partial re-run.
  async membershipsSignupSubmitted(page) {
    await login(page);
    await openApplyIndividual(page);
    await selectFirstMembershipOption(page);
    await clearMailpit();
    await registerMembership(page);
  },

  // Relies on membershipsSignupSubmitted (just before this one) having
  // already created the pending application earlier in this same run.
  async membershipsApprovalPending(page) {
    await login(page);
    await openFirstIndividualMembership(page);
  },

  async membershipsApprovalApproved(page) {
    await login(page);
    await openFirstIndividualMembership(page);
    await approveViaTodayNow(page);
    await saveAdminFormContinueEditing(page);
  },

  // Relies on membershipsSignupSubmitted having already cleared Mailpit and
  // triggered exactly two emails earlier in this same run -- this step only
  // views the result, it doesn't send anything itself.
  //
  // Screenshots just the rendered email itself (the #preview-html iframe's
  // real content), not the surrounding Mailpit inbox/tabs/sidebar chrome --
  // a client reader only ever needs to know what the *email* looks like, and
  // Mailpit's own UI (a local-dev-only tool that doesn't exist on their live
  // site) would otherwise be the most visually prominent thing in the image.
  // Returning true tells main() this step already wrote its own screenshot,
  // skipping the usual whole-viewport capture.
  //
  // A plain `locator.screenshot()` on the iframe (tried first) produced two
  // visible problems: a 1-2px dark line along the very top edge, and a large
  // blank gap at the bottom. Both come from the same cause -- the iframe
  // element's own box is a fixed 919px tall regardless of the email's actual
  // length (Mailpit/MJML fill it for background-colour consistency), so an
  // automatic element screenshot clips to that fixed box: its top edge lands
  // exactly on the boundary with Mailpit's tab bar above it (a fractional
  // clip coordinate rounds the wrong way and grabs a sliver of the tab bar's
  // dark border), and its bottom extends ~80px past the email's real last
  // line of text into empty filler space. Taking an explicit `page.screenshot`
  // with a manually computed `clip` fixes both: starting 2px below the
  // iframe's own top (skips the tab-bar sliver) and ending just below the
  // real content's lowest text (found via `getIframeContentBottom`, not the
  // iframe's own height) plus a little breathing room.
  //
  // This needs a taller viewport than the suite's usual 1280x800 -- the
  // clip region this produces is taller than 800px, and Chromium silently
  // truncates a `clip` that extends past the page's current viewport rather
  // than rendering past it. Only this page instance's viewport changes
  // (each capture step gets its own fresh page in main()'s loop), so this
  // doesn't affect any other screenshot's fixed-viewport determinism.
  async membershipsStaffNotification(page, outPath) {
    await page.setViewportSize({ width: VIEWPORT.width, height: 1600 });
    const messageId = await getMailpitMessageIdByFrom("webmaster@localhost");
    await page.goto(`${MAILPIT_ORIGIN}/view/${messageId}`);
    await page.waitForLoadState("networkidle");
    const box = await page.locator("#preview-html").boundingBox();
    const contentBottom = await getIframeContentBottom(page, "#preview-html");
    const TOP_INSET = 2;
    const BOTTOM_PADDING = 24;
    await page.screenshot({
      path: outPath,
      clip: {
        x: box.x,
        y: box.y + TOP_INSET,
        width: box.width,
        height: Math.min(contentBottom - TOP_INSET + BOTTOM_PADDING, box.height - TOP_INSET),
      },
    });
    return true;
  },
};
