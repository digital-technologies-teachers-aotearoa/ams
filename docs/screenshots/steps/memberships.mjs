// Memberships (tutorial 6). Membership options are managed in the Django
// admin, not the CMS -- these steps build on each other in the same way
// branding/first-pages' state-changing steps do: this tutorial's own option
// and application only exist once earlier steps in manifest.json's order
// have created them in this run.

import { BASE_URL } from "../shared/config.mjs";
import {
  login,
  saveAdminForm,
  saveAdminFormContinueEditing,
  scrollIntoViewInstantly,
  clearMailpit,
  screenshotMailpitEmail,
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
  // views the result, it doesn't send anything itself. Returning true tells
  // main() this step already wrote its own screenshot (via
  // screenshotMailpitEmail), skipping the usual whole-viewport capture.
  async membershipsStaffNotification(page, outPath) {
    await screenshotMailpitEmail(page, outPath, "webmaster@localhost");
    return true;
  },
};
