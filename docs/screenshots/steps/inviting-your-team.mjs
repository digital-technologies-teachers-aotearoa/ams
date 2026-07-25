// Inviting your team (tutorial 10). New team member accounts are created in
// the Django admin, not the CMS -- Wagtail's own /cms/users/new/ form was
// tried first and rejected after live testing: its fields are derived from
// User.USERNAME_FIELD ("email" in this project) union a fixed standard set
// (email, first_name, last_name, is_superuser, groups), so it never collects
// AMS's own separate `username` field. A user created that way is left with
// a blank username, and UserRedirectView (ams/users/views.py) reverses
// "users:detail" using request.user.username straight after login --
// confirmed live: signing in as a user created this way immediately hits a
// NoReverseMatch 500 at /users/~redirect/. Django admin's add-user form
// (UserAdminCreationForm, ams/users/forms.py) explicitly includes username
// as a required field, so it doesn't hit this bug.

import { BASE_URL, MAILPIT_ORIGIN } from "../shared/config.mjs";
import {
  login,
  loginAs,
  clearMailpit,
  getMailpitMessageIdByFrom,
  screenshotMailpitEmail,
  scrollIntoViewInstantly,
} from "../shared/browser-helpers.mjs";

const TEAMMATE_EMAIL = "jordan@example.org";
const TEAMMATE_PASSWORD = "Correct-Horse-Battery-Staple-42";
const TEAMMATE_FIRST_NAME = "Jordan";
const TEAMMATE_LAST_NAME = "Lee";
const TEAMMATE_USERNAME = "jordanlee";
const CONFIRMATION_EMAIL_FROM = "webmaster@localhost";

async function openUserAdd(page) {
  await page.goto(`${BASE_URL}/admin/users/user/add/`);
  await page.waitForLoadState("networkidle");
}

async function fillUserAddForm(page) {
  await page.getByRole("textbox", { name: "Email address:" }).fill(TEAMMATE_EMAIL);
  await page.getByRole("textbox", { name: "Password:", exact: true }).fill(TEAMMATE_PASSWORD);
  await page
    .getByRole("textbox", { name: "Password confirmation:" })
    .fill(TEAMMATE_PASSWORD);
  await page.getByRole("textbox", { name: "First name:" }).fill(TEAMMATE_FIRST_NAME);
  await page.getByRole("textbox", { name: "Last name:" }).fill(TEAMMATE_LAST_NAME);
  await page.getByRole("textbox", { name: "Username:" }).fill(TEAMMATE_USERNAME);
}

async function submitUserAddForm(page) {
  await page.getByRole("button", { name: "Save", exact: true }).click();
  await page.waitForLoadState("networkidle");
}

// This run's only new user, so its own email is always the right row to
// open -- the same "only one exists" simplification resources.mjs's
// openTheResource relies on.
async function openTeammateChangePage(page) {
  await page.goto(`${BASE_URL}/admin/users/user/`);
  await page.waitForLoadState("networkidle");
  await page.getByRole("link", { name: TEAMMATE_EMAIL }).click();
  await page.waitForLoadState("networkidle");
}

// The Groups widget is Django admin's classic filter_horizontal
// (SelectFilter2). A real double-click was tried first (the same
// double-click-to-choose interaction confirmed live for the Author field in
// resources.mjs) and rejected after it proved unreliable here specifically:
// SelectBox.js (Django's own admin/js/SelectBox.js) keeps an in-memory
// `cache` per select, entirely separate from the live DOM, and every
// `redisplay()` -- including the one SelectFilter2's own move handler calls
// right after moving an option -- rebuilds the visible <option>s from that
// cache, not from whatever the DOM currently holds. A double-click that
// lands before the cache work finishes (or any direct DOM edit, tried next
// and also rejected -- confirmed by reading SelectBox.js) gets silently
// discarded the moment anything redisplays the box, with no error and no
// visible sign at click time; the empty "Chosen groups" list only shows up
// once the saved record reloads, by which point there's nothing left to
// debug at the click site. Calling Django's own exposed `window.SelectBox`
// API directly -- the same function SelectFilter2's move button and
// double-click handler both call internally -- updates cache and DOM
// together and isn't subject to either failure mode. Confirmed live: a
// plain double-click intermittently left the option in "Available groups"
// with no error, silently saving an empty groups list; this doesn't.
async function grantEditorAccess(page) {
  await page.getByRole("checkbox", { name: "Staff status" }).check();
  await page.evaluate(() => {
    const opt = Array.from(document.getElementById("id_groups_from").options).find(
      (o) => o.text === "Editors",
    );
    opt.selected = true;
    window.SelectBox.move("id_groups_from", "id_groups_to");
  });
}

// Scrolls the Permissions fieldset's Groups widget into view after saving --
// it sits below Email, Password, and Personal info, so a screenshot taken
// right after a reload would show the top of the page instead of the
// Staff-status-and-Editors state this step exists to show, the same fix
// publishResource() (resources.mjs) applies for the same reason.
async function saveChangeFormContinueEditing(page) {
  await page.getByRole("button", { name: "Save and continue editing" }).first().click();
  await page.waitForLoadState("networkidle");
  await scrollIntoViewInstantly(page.getByRole("checkbox", { name: "Staff status" }));
}

// Fetches the already-sent confirmation email's own text body (via Mailpit's
// HTTP API, from the script's own Node process -- no page needed) and clicks
// through the real emailed link, exactly what a real new team member does.
// Assumes invitingConfirmationEmail already triggered and cleared Mailpit
// down to this one message earlier in this same run.
async function confirmTeammateEmail(page) {
  const messageId = await getMailpitMessageIdByFrom(CONFIRMATION_EMAIL_FROM);
  const detailRes = await fetch(`${MAILPIT_ORIGIN}/api/v1/message/${messageId}`);
  const detail = await detailRes.json();
  const confirmPath = detail.Text.match(/\/en\/accounts\/confirm-email\/\S+\//)[0];
  await page.goto(`${BASE_URL}${confirmPath}`);
  await page.getByRole("button", { name: "Confirm" }).click();
  await page.waitForLoadState("networkidle");
}

export const steps = {
  async invitingFormEmpty(page) {
    await login(page);
    await openUserAdd(page);
  },

  async invitingUserCreated(page) {
    await login(page);
    await openUserAdd(page);
    await fillUserAddForm(page);
    await submitUserAddForm(page);
  },

  // Relies on invitingUserCreated (just before this one) having already
  // created the account earlier in this same run.
  async invitingPermissionsSaved(page) {
    await login(page);
    await openTeammateChangePage(page);
    await grantEditorAccess(page);
    await saveChangeFormContinueEditing(page);
  },

  // Relies on invitingUserCreated + invitingPermissionsSaved having already
  // run earlier in this same run. Clears Mailpit, then attempts to sign in
  // as the new teammate -- confirmed live that no confirmation email is
  // sent at account-creation time; ACCOUNT_EMAIL_VERIFICATION = "mandatory"
  // (config/settings/base.py) means this sign-in attempt doesn't log them
  // in yet, it triggers a fresh confirmation email instead, which is what
  // this step then screenshots. Returning true tells main() this step
  // already wrote its own screenshot (via screenshotMailpitEmail), skipping
  // the usual whole-viewport capture.
  async invitingConfirmationEmail(page, outPath) {
    await clearMailpit();
    await loginAs(page, TEAMMATE_EMAIL, TEAMMATE_PASSWORD);
    await screenshotMailpitEmail(page, outPath, CONFIRMATION_EMAIL_FROM);
    return true;
  },

  // Relies on invitingConfirmationEmail having already triggered and sent
  // the confirmation email earlier in this same run. Confirms it via the
  // real emailed link, then signs in for real, on this step's own fresh,
  // not-yet-authenticated page -- each manifest entry gets a new page
  // (run.mjs's main() loop), so there's no earlier session to sign out of
  // first.
  async invitingStaffLinks(page) {
    await confirmTeammateEmail(page);
    await loginAs(page, TEAMMATE_EMAIL, TEAMMATE_PASSWORD);
    await scrollIntoViewInstantly(page.getByRole("heading", { name: "Staff links" }));
  },
};
