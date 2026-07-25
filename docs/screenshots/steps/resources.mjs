// Resources (tutorial 9). AMS_RESOURCES_ENABLED is already True in this dev
// environment's .envs/.local/django.ini, so no runtime settings change is
// needed to capture these steps -- unlike a real client, where it's an
// operator-set env var (see the tutorial's own "Before you start"), the same
// pattern events.mjs's own top comment already established for its flag.

import { BASE_URL, ADMIN_EMAIL } from "../shared/config.mjs";
import {
  login,
  saveAdminForm,
  saveAdminFormContinueEditing,
  scrollIntoViewInstantly,
  fillTinyMce,
} from "../shared/browser-helpers.mjs";

const RESOURCE_NAME = "Year 9 Assessment Rubric";
const RESOURCE_DESCRIPTION =
  "A rubric for assessing Year 9 maths projects, ready to adapt for your own classes.";
const RESOURCE_COMPONENT_NAME = "Download the rubric";
const RESOURCE_COMPONENT_URL = "https://example.org/year-9-assessment-rubric";

async function openResourceAdd(page) {
  await page.goto(`${BASE_URL}/admin/resources/resource/add/`);
  await page.waitForLoadState("networkidle");
}

// The Author users/entities widget is Django admin's classic filter_horizontal
// (SelectFilter2), a pair of plain <select multiple> elements
// (#id_author_users_from / _to) enhanced with search boxes -- a real admin's
// double-click on an available option is what moves it across, confirmed live
// (a single click alone only highlights it). Picks the seed superuser itself
// (ADMIN_EMAIL), the only user that exists on a freshly seed.sh-seeded site,
// the same "only one exists" simplification events.mjs's openTheEvent uses.
async function chooseAuthorUser(page) {
  await page
    .locator("#id_author_users_from")
    .getByRole("option", { name: ADMIN_EMAIL })
    .dblclick();
}

async function fillResourceForm(page) {
  await page.locator("#id_name_en").fill(RESOURCE_NAME);
  await fillTinyMce(page, "id_description_en", `<p>${RESOURCE_DESCRIPTION}</p>`);
  await chooseAuthorUser(page);
  await page.locator("#id_components-0-name_en").fill(RESOURCE_COMPONENT_NAME);
  await page.locator("#id_components-0-component_url").fill(RESOURCE_COMPONENT_URL);
}

// This run's only resource, so its own name is always the right row to open --
// the same simplification openTheEvent (events.mjs) relies on.
async function openTheResource(page) {
  await page.goto(`${BASE_URL}/admin/resources/resource/`);
  await page.waitForLoadState("networkidle");
  await page.getByRole("link", { name: RESOURCE_NAME }).click();
  await page.waitForLoadState("networkidle");
}

// Scrolls the Published checkbox into view after saving -- the Visibility
// fieldset it's in sits below Name, Description, Ownership and Tags, so a
// screenshot taken right after a reload would show the top of the page
// instead of the checkbox this step exists to show, the same fix
// publishEvent() (events.mjs) already applies for the same reason.
async function publishResource(page) {
  await page.getByRole("checkbox", { name: "Published" }).check();
  await saveAdminFormContinueEditing(page);
  await scrollIntoViewInstantly(page.getByRole("checkbox", { name: "Published" }));
}

export const steps = {
  async resourcesFormEmpty(page) {
    await login(page);
    await openResourceAdd(page);
  },

  async resourcesFormSaved(page) {
    await login(page);
    await openResourceAdd(page);
    await fillResourceForm(page);
    await saveAdminForm(page);
  },

  // Relies on resourcesFormSaved (just before this one) having already
  // created the resource earlier in this same run.
  async resourcesPublished(page) {
    await login(page);
    await openTheResource(page);
    await publishResource(page);
  },

  // Relies on resourcesPublished (just before this one) having already
  // published the resource earlier in this same run.
  async resourcesLive(page) {
    await login(page);
    await page.goto(`${BASE_URL}/en/resources/`);
    await page.waitForLoadState("networkidle");
  },

  // Relies on resourcesPublished, same as resourcesLive above.
  async resourcesDetail(page) {
    await login(page);
    await page.goto(`${BASE_URL}/en/resources/`);
    await page.waitForLoadState("networkidle");
    await page.getByRole("link", { name: RESOURCE_NAME }).click();
    await page.waitForLoadState("networkidle");
  },
};
