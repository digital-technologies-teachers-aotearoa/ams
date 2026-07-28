// Forum (tutorial 8). Discourse itself is not reset by seed.sh -- it has its
// own database, entirely separate from Django's, so category/topic content
// created here would persist (and, if steps posted anything, accumulate)
// across every future run of this suite forever. Every forum step below is
// deliberately read-only on the Discourse side (view categories, view the
// empty New category form without submitting it) for exactly that reason --
// see docs-conventions.md's "Discourse baseline" note under "How to
// regenerate screenshots" for the resulting assumption this suite makes
// about Discourse's starting state.

import { BASE_URL, DISCOURSE_ORIGIN } from "../shared/config.mjs";
import { login, loginAs, logout } from "../shared/browser-helpers.mjs";

const NO_MEMBERSHIP_USER_EMAIL = "demo.member@ams-demo.test";
const NO_MEMBERSHIP_USER_PASSWORD = "Demo-Member-Forum-26";
const NO_MEMBERSHIP_USER_USERNAME = "demo_member";

// Carries an already-logged-in-to-AMS page through the same `/forum/`
// SSO entry point a real "visit your forum" link would use, landing on
// Discourse's own home page signed in as that AMS account.
// Waits for "load", not this suite's usual "networkidle" -- confirmed live
// that Discourse's own Ember app keeps a background connection open (for
// live update polling) that never goes idle, so "networkidle" reliably timed
// out here even once the page had genuinely finished rendering.
async function loginToForum(page) {
  await page.goto(`${BASE_URL}/forum/`);
  await page.waitForLoadState("load");
}

// Creates a second AMS account with no membership at all, for the "member
// without an active membership" screenshot -- the admin account used
// throughout the rest of this suite can't demonstrate that gate (see the
// comment on logout() in browser-helpers.mjs). Built entirely through
// Django admin forms (Add user, then Add email address) rather than the
// public signup form: this tutorial isn't teaching account signup, only
// what the forum's own membership gate looks like, and
// ACCOUNT_EMAIL_VERIFICATION="mandatory" means a real signup would need its
// own confirmation-email/Mailpit round trip for no benefit here. Django's
// UserAdmin.response_add() always redirects to the new user's own change
// page after saving (a Django default specific to UserAdmin, unlike every
// other ModelAdmin), which is what lets this read the new user's id
// straight back off the URL.
async function createNoMembershipUser(page) {
  await page.goto(`${BASE_URL}/admin/users/user/add/`);
  await page.waitForLoadState("networkidle");
  await page.getByRole("textbox", { name: "Email address:" }).fill(NO_MEMBERSHIP_USER_EMAIL);
  await page
    .getByRole("textbox", { name: "Password:", exact: true })
    .fill(NO_MEMBERSHIP_USER_PASSWORD);
  await page
    .getByRole("textbox", { name: "Password confirmation:" })
    .fill(NO_MEMBERSHIP_USER_PASSWORD);
  await page.getByRole("textbox", { name: "First name:" }).fill("Demo");
  await page.getByRole("textbox", { name: "Last name:" }).fill("Member");
  await page.getByRole("textbox", { name: "Username:" }).fill(NO_MEMBERSHIP_USER_USERNAME);
  await page.getByRole("button", { name: "Save", exact: true }).click();
  await page.waitForLoadState("networkidle");
  const userId = page.url().match(/\/user\/(\d+)\/change\//)[1];

  await page.goto(`${BASE_URL}/admin/account/emailaddress/add/`);
  await page.waitForLoadState("networkidle");
  await page.getByRole("textbox", { name: "User:" }).fill(userId);
  await page.getByRole("textbox", { name: "Email address:" }).fill(NO_MEMBERSHIP_USER_EMAIL);
  await page.getByRole("checkbox", { name: "Verified" }).check();
  await page.getByRole("checkbox", { name: "Primary" }).check();
  await page.getByRole("button", { name: "Save", exact: true }).click();
  await page.waitForLoadState("networkidle");
}

export const steps = {
  // Deliberately does not call login() -- the same "no explicit logout
  // needed, browser.newPage() is already signed out" pattern
  // languages-translations.mjs established, and the point of this specific
  // step is what an unauthenticated visit to the forum actually does
  // (redirects into AMS's own sign-in page).
  async forumSignInPrompt(page) {
    await page.goto(`${BASE_URL}/forum/`);
    await page.waitForLoadState("networkidle");
  },

  async forumHome(page) {
    await login(page);
    await loginToForum(page);
  },

  async forumCategories(page) {
    await login(page);
    await loginToForum(page);
    await page.goto(`${DISCOURSE_ORIGIN}/categories`);
    await page.waitForLoadState("load");
  },

  // Read-only: opens the New category form but never submits it, so this
  // step never adds to Discourse's own persisted category list -- see the
  // "Forum" comment above.
  async forumNewCategoryForm(page) {
    await login(page);
    await loginToForum(page);
    await page.goto(`${DISCOURSE_ORIGIN}/new-category`);
    await page.waitForLoadState("load");
  },

  // Self-contained: creates its own second AMS account (with no membership
  // at all) rather than depending on any earlier step, since no other
  // screenshot in this suite needs one. Never reaches Discourse -- the
  // membership gate in ams/forum/views.py's forum_sso_login_callback runs
  // and redirects before the SSO handshake with Discourse even starts.
  async forumMembershipRequired(page) {
    await login(page);
    await createNoMembershipUser(page);
    await logout(page);
    await loginAs(page, NO_MEMBERSHIP_USER_EMAIL, NO_MEMBERSHIP_USER_PASSWORD);
    await page.goto(`${BASE_URL}/forum/`);
    await page.waitForLoadState("networkidle");
  },
};
