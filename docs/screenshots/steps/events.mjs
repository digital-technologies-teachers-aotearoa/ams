// Events (tutorial 8). AMS_EVENTS_ENABLED is already True in this dev
// environment's .envs/.local/django.ini, so no runtime settings change is
// needed to capture these steps -- unlike a real client, where it's an
// operator-set env var (see the tutorial's own "Before you start").

import { BASE_URL } from "../shared/config.mjs";
import {
  login,
  saveAdminForm,
  saveAdminFormContinueEditing,
  scrollIntoViewInstantly,
} from "../shared/browser-helpers.mjs";

const EVENT_LOCATION_NAME = "Wellington Conference Centre";
const EVENT_LOCATION_CITY = "Wellington";
const EVENT_NAME = "Annual Conference";
const EVENT_DESCRIPTION =
  "Our annual gathering for maths teachers, with workshops and a keynote speaker.";
const EVENT_SESSION_NAME = "Conference Day";
const EVENT_SESSION_DESCRIPTION =
  "Workshops, a keynote speaker, and time to connect with other teachers.";
const EVENT_REGISTRATION_LINK = "https://forms.example.org/annual-conference";
const EVENT_SESSION_START_TIME = "09:00:00";
const EVENT_SESSION_END_TIME = "16:00:00";
// Comfortably far ahead that a capture run never has to race the session's
// own start time -- see futureDateISO() below for why this is computed
// fresh on every run rather than a fixed date.
const EVENT_SESSION_DAYS_AHEAD = 60;

// A session needs a real future start/end, not a fixed date -- a hard-coded
// one would eventually become "past" and drop off the public Upcoming
// events listing these steps capture, the same "don't hard-code something
// that goes stale" instinct as browser-helpers.mjs's getEnglishHomePageId
// runtime lookup, applied to a date instead of a database ID. Computed fresh
// on every run, comfortably ahead (EVENT_SESSION_DAYS_AHEAD) so a slow
// capture run never has to race its own start time.
// Built from local date parts (getFullYear/getMonth/getDate), not
// toISOString() (which is UTC) -- avoids an off-by-one day near midnight in
// whatever timezone this script happens to run in.
function futureDateISO(daysAhead) {
  const d = new Date();
  d.setDate(d.getDate() + daysAhead);
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

async function openLocationAdd(page) {
  await page.goto(`${BASE_URL}/admin/events/location/add/`);
  await page.waitForLoadState("networkidle");
}

async function fillLocationForm(page) {
  await page.locator("#id_name_en").fill(EVENT_LOCATION_NAME);
  await page.locator("#id_city").fill(EVENT_LOCATION_CITY);
}

async function openEventAdd(page) {
  await page.goto(`${BASE_URL}/admin/events/event/add/`);
  await page.waitForLoadState("networkidle");
}

// TinyMCE (the Description fields' rich text widget here, unlike Draftail
// elsewhere in this suite -- see browser-helpers.mjs's fillBodyText comment)
// exposes an editor API rather than a plain contenteditable, and
// setContent() is its own documented way to set content programmatically.
// Confirmed live: this syncs the underlying hidden textarea a form submit
// actually reads from immediately, with none of fillBodyText's debounce
// race to guard against.
async function fillTinyMce(page, fieldId, html) {
  await page.evaluate(
    ({ fieldId, html }) => window.tinymce.get(fieldId).setContent(html),
    { fieldId, html },
  );
}

// The Locations field (django-autocomplete-light) opens a search-as-you-type
// listbox rather than a plain <select> -- typing the location's name and
// picking the one matching option is what a real admin's click does.
// getByRole("option", { name }) matches by substring by default (not exact),
// so the option's full "name, city" text still matches on name alone.
async function selectEventLocation(page, name) {
  const group = page.getByRole("group", { name: "Location" });
  await group.getByRole("searchbox").click();
  await group.getByRole("searchbox").pressSequentially(name);
  await page.getByRole("option", { name }).click();
}

async function fillEventForm(page) {
  await page.locator("#id_name_en").fill(EVENT_NAME);
  await fillTinyMce(page, "id_description_en", `<p>${EVENT_DESCRIPTION}</p>`);
  await selectEventLocation(page, EVENT_LOCATION_NAME);
  await page.locator("#id_registration_link").fill(EVENT_REGISTRATION_LINK);
  await page.locator("#id_sessions-0-name_en").fill(EVENT_SESSION_NAME);
  await fillTinyMce(
    page,
    "id_sessions-0-description_en",
    `<p>${EVENT_SESSION_DESCRIPTION}</p>`,
  );
  const sessionDate = futureDateISO(EVENT_SESSION_DAYS_AHEAD);
  await page.locator("#id_sessions-0-start_0").fill(sessionDate);
  await page.locator("#id_sessions-0-start_1").fill(EVENT_SESSION_START_TIME);
  await page.locator("#id_sessions-0-end_0").fill(sessionDate);
  await page.locator("#id_sessions-0-end_1").fill(EVENT_SESSION_END_TIME);
}

// This run's only event, so its own name is always the right row to open --
// the same "only one exists" simplification memberships.mjs's
// openFirstIndividualMembership relies on.
async function openTheEvent(page) {
  await page.goto(`${BASE_URL}/admin/events/event/`);
  await page.waitForLoadState("networkidle");
  await page.getByRole("link", { name: EVENT_NAME }).click();
  await page.waitForLoadState("networkidle");
}

// Scrolls the Published checkbox into view after saving -- the Visibility
// fieldset it's in sits well below the fold (Name, Description, Series,
// Organisers, Sponsors, Price, Location and Registration all come first),
// so a screenshot taken right after a reload would show the top of the page
// instead of the very checkbox this step exists to show, the same class of
// fix as scrollIntoViewInstantly's other callers.
async function publishEvent(page) {
  await page.getByRole("checkbox", { name: "Published" }).check();
  await saveAdminFormContinueEditing(page);
  await scrollIntoViewInstantly(page.getByRole("checkbox", { name: "Published" }));
}

export const steps = {
  async eventsLocationFormEmpty(page) {
    await login(page);
    await openLocationAdd(page);
  },

  async eventsLocationSaved(page) {
    await login(page);
    await openLocationAdd(page);
    await fillLocationForm(page);
    await saveAdminForm(page);
  },

  // Relies on eventsLocationSaved (just before this one) having already
  // created the location earlier in this same run.
  async eventsEventFormEmpty(page) {
    await login(page);
    await openEventAdd(page);
  },

  async eventsEventSaved(page) {
    await login(page);
    await openEventAdd(page);
    await fillEventForm(page);
    await saveAdminForm(page);
  },

  // Relies on eventsEventSaved (just before this one) having already
  // created the event earlier in this same run.
  async eventsEventPublished(page) {
    await login(page);
    await openTheEvent(page);
    await publishEvent(page);
  },

  // Relies on eventsEventPublished (just before this one) having already
  // published the event earlier in this same run.
  async eventsEventLive(page) {
    await login(page);
    await page.goto(`${BASE_URL}/en/events/`);
    await page.waitForLoadState("networkidle");
  },

  // Relies on eventsEventPublished, same as eventsEventLive above.
  async eventsEventDetail(page) {
    await login(page);
    await page.goto(`${BASE_URL}/en/events/`);
    await page.waitForLoadState("networkidle");
    await page.getByRole("link", { name: EVENT_NAME }).click();
    await page.waitForLoadState("networkidle");
  },
};
