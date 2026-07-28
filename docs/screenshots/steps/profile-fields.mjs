// Custom profile fields (tutorial 7). Profile field groups and fields are
// managed in the Django admin, not the CMS -- these steps build on each
// other in the same way memberships.mjs's own state-changing steps do: the
// group and field this tutorial documents only exist once earlier steps in
// manifest.json's order have created them in this run.
//
// Both custom widgets involved (TranslationWidget, OptionsWidget --
// ams/users/widgets.py) turned out not to need any of the Draftail/Wagtail-
// specific handling docs-conventions.md bullets 11/15/18 warn about:
// confirmed live that TranslationWidget's per-language inputs are read
// straight off the submitted POST data by value_from_datadict() (not from
// the hidden input its own JS also populates, which is unused dead code as
// far as saving goes), and OptionsWidget's hidden input is kept in sync by a
// plain `input` event listener that a real Playwright `.fill()` already
// dispatches -- so ordinary `.fill()`/`.selectOption()` on the visible
// inputs is sufficient for both, with no debounce or editor-API workaround
// needed.

import { BASE_URL } from "../shared/config.mjs";
import { login, saveAdminForm, scrollIntoViewInstantly } from "../shared/browser-helpers.mjs";

const GROUP_NAME = "Teaching details";
const FIELD_KEY = "teaching_subject";
const FIELD_LABEL = "Which subject do you mainly teach?";
const FIELD_HELP_TEXT =
  "Helps us match you with subject-specific resources and events.";
const FIELD_CHOICES = [
  ["mathematics", "Mathematics"],
  ["science", "Science"],
  ["english", "English"],
  ["other", "Other"],
];
const ANSWER_LABEL = "Mathematics";

async function openGroupAdd(page) {
  await page.goto(`${BASE_URL}/admin/users/profilefieldgroup/add/`);
  await page.waitForLoadState("networkidle");
}

async function fillGroupForm(page) {
  await page.locator('input[name="name_translations_en"]').fill(GROUP_NAME);
}

async function openFieldAdd(page) {
  await page.goto(`${BASE_URL}/admin/users/profilefield/add/`);
  await page.waitForLoadState("networkidle");
}

// Adds one "Add Choice" row per extra choice beyond the one the widget
// already starts with (options_widget.js's initWidget adds a single empty
// row when there's no initial data), then fills every row's Value and
// English label -- the Te Reo Māori column is left blank, the same
// single-language simplification the group's own name uses (see
// profile-fields.md's "Before you start" for why).
async function fillFieldForm(page) {
  await page.locator('input[name="field_key"]').fill(FIELD_KEY);
  await page.locator("#id_group").selectOption({ label: GROUP_NAME });
  await page.locator("#id_field_type").selectOption({ label: "Select" });
  await page.locator('input[name="label_translations_en"]').fill(FIELD_LABEL);
  await page
    .locator('input[name="help_text_translations_en"]')
    .fill(FIELD_HELP_TEXT);

  for (let i = 1; i < FIELD_CHOICES.length; i++) {
    await page.getByRole("button", { name: "Add Choice" }).click();
  }

  const rows = page.locator(".options-widget .options-table-body tr");
  for (let i = 0; i < FIELD_CHOICES.length; i++) {
    const [value, label] = FIELD_CHOICES[i];
    const row = rows.nth(i);
    await row.locator(".option-value").fill(value);
    // Column order follows AMS_ENABLED_LANGUAGES (Te Reo Māori, then
    // English in this env), so English is the second .option-label input
    // in each row -- see options_widget.html's thead, built from the same
    // settings.LANGUAGES order.
    await row.locator(".option-label").nth(1).fill(label);
  }

  await page.locator("#id_is_required_for_membership").check();
}

async function openUpdateForm(page) {
  await page.goto(`${BASE_URL}/en/users/~update/`);
  await page.waitForLoadState("networkidle");
}

export const steps = {
  async profileFieldsGroupFormEmpty(page) {
    await login(page);
    await openGroupAdd(page);
  },

  async profileFieldsGroupSaved(page) {
    await login(page);
    await openGroupAdd(page);
    await fillGroupForm(page);
    await saveAdminForm(page);
  },

  // Relies on profileFieldsGroupSaved (just before this one) having already
  // created the Teaching details group earlier in this same run, so it's
  // available in the Group dropdown.
  async profileFieldsFieldFormEmpty(page) {
    await login(page);
    await openFieldAdd(page);
  },

  async profileFieldsFieldSaved(page) {
    await login(page);
    await openFieldAdd(page);
    await fillFieldForm(page);
    await saveAdminForm(page);
  },

  // Relies on profileFieldsFieldSaved having already created the field
  // earlier in this same run, so the account page has something unanswered
  // to nudge about. login() itself lands on the account page
  // (LOGIN_REDIRECT_URL = "users:redirect" -> users:detail), so no
  // further navigation is needed.
  async profileFieldsAccountNudge(page) {
    await login(page);
  },

  // Scrolls the new group's fieldset into view -- it's the last one on the
  // form, below Personal Information, so a screenshot taken right after
  // load would show the top of the page instead.
  async profileFieldsUpdateForm(page) {
    await login(page);
    await openUpdateForm(page);
    await scrollIntoViewInstantly(page.getByRole("group", { name: GROUP_NAME }));
  },

  // Relies on profileFieldsFieldSaved having already created the field
  // earlier in this same run. Answers it and saves, which redirects back to
  // the account page with the nudge gone -- the same "mutate, then view the
  // result" shape as memberships.mjs's own signup/approval steps.
  async profileFieldsAccountComplete(page) {
    await login(page);
    await openUpdateForm(page);
    await page.locator("#id_teaching_subject").selectOption({ label: ANSWER_LABEL });
    await page.getByRole("button", { name: "Update Profile" }).click();
    await page.waitForLoadState("networkidle");
  },
};
