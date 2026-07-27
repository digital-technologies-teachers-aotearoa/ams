// Marketing screenshots for features.md, requested as a deliberate departure
// from the rest of the suite: richer, more populated, and cropped/composed
// for visual impact rather than for teaching a real client's empty site.
// A DIFFERENT seed script backs these -- docs/screenshots/seed-marketing.sh,
// not seed.sh -- since they need `sample_data`-style fixture content
// (dozens of events/resources, a fully-blocked homepage, a multi-period
// billing history) that the tutorial suite's deliberately-empty skeleton
// doesn't have and shouldn't grow just for this one page. Run with
// `npm run docs:screenshots -- marketing` against a database seeded by
// seed-marketing.sh -- never against the plain seed.sh skeleton the rest of
// the suite uses, and never mixed into a full unfiltered
// `npm run docs:screenshots` run.
//
// The Community Forum screenshot is the one genuine exception to this
// suite's "stay read-only on Discourse" rule (docs-conventions.md bullet
// 23) -- see docs/screenshots/fixtures/marketing_forum_content.rb's own
// comment for why that's a deliberate, permanent departure for this one
// screenshot rather than an oversight.

import fs from 'node:fs';
import path from 'node:path';
import {
  BASE_URL,
  VIEWPORT,
  SCREENSHOTS_ROOT,
  DEVICE_SCALE_FACTOR,
} from '../shared/config.mjs';
import {
  login,
  getEnglishHomePageId,
  prepareForCapture,
  proxyMinioMedia,
  insertBodyBlock,
  fillBodyText,
  saveDraft,
} from '../shared/browser-helpers.mjs';

const DEMO_ORG_NAME = 'Mathematics Teachers Association';
const NAVBAR_1_LOGO_FIXTURE = path.join(
  SCREENSHOTS_ROOT,
  'fixtures',
  'demo-theme-example-1.png'
);
const NAVBAR_3_LOGO_FIXTURE = path.join(
  SCREENSHOTS_ROOT,
  'fixtures',
  'demo-theme-example-3.svg'
);

const MEMBERSHIP_OPTIONS = [
  {
    name: 'Student',
    durationNum: '6',
    durationUnit: 'Months',
    cost: '25',
    invoiceRef: 'MTA Membership',
    votingRights: false,
  },
  {
    name: 'Standard',
    durationNum: '1',
    durationUnit: 'Years',
    cost: '75',
    invoiceRef: 'MTA Membership',
  },
  {
    name: 'Wider Education Sector',
    durationNum: '1',
    durationUnit: 'Years',
    cost: '199',
    invoiceRef: 'MTA Membership',
    invoiceDueDays: '100',
  },
];

async function setAssociationName(page) {
  await page.goto(`${BASE_URL}/cms/settings/cms/associationsettings/`);
  await page.waitForLoadState('networkidle');
  await page.locator('#id_association_short_name').fill(DEMO_ORG_NAME);
  await page.locator('#id_association_long_name').fill(DEMO_ORG_NAME);
  await page.getByRole('button', { name: 'Save' }).click();
  await page.waitForLoadState('networkidle');
}

async function createMembershipOption(page, option) {
  await page.goto(`${BASE_URL}/admin/memberships/membershipoption/add/`);
  await page.waitForLoadState('networkidle');
  await page.getByRole('textbox', { name: 'Name:' }).fill(option.name);
  await page.locator('#id_duration_0').fill(option.durationNum);
  await page.locator('#id_duration_1').selectOption(option.durationUnit);
  await page.getByRole('spinbutton', { name: 'Cost:' }).fill(option.cost);
  await page
    .getByRole('textbox', { name: 'Invoice Reference:' })
    .fill(option.invoiceRef);
  if (option.votingRights === false) {
    await page.getByRole('checkbox', { name: 'Voting rights' }).uncheck();
  }
  if (option.invoiceDueDays) {
    await page
      .getByRole('spinbutton', { name: 'Invoice Due Days:' })
      .fill(option.invoiceDueDays);
  }
  await page.getByRole('button', { name: 'Save', exact: true }).first().click();
  await page.waitForLoadState('networkidle');
}

// Clips from an element's top to another element's bottom, in full-page
// (not viewport-relative) coordinates -- callers set a tall-enough viewport
// first so the whole region is already rendered without scrolling, the same
// approach screenshotMailpitEmail (shared/browser-helpers.mjs) uses for a
// similarly hand-picked crop. topPad/bottomPad are separate (not one shared
// padding) because the default 24px topPad still let the breadcrumb above
// "Apply for Membership"'s own heading bleed into frame -- found live, not
// every page has the same gap between its breadcrumb and its own heading.
async function clipBetween(
  page,
  outPath,
  topLocator,
  bottomLocator,
  { topPad = 24, bottomPad = 24 } = {}
) {
  const top = await topLocator.boundingBox();
  const bottom = await bottomLocator.boundingBox();
  await page.screenshot({
    path: outPath,
    clip: {
      x: 0,
      y: Math.max(top.y - topPad, 0),
      width: VIEWPORT.width,
      height: bottom.y + bottom.height - top.y + topPad + bottomPad,
    },
  });
}

// Crops a page's own main content -- everything between the breadcrumb nav
// and the footer -- excluding the header, breadcrumbs, and footer
// themselves. Every page in this suite shares the same base.html structure
// (header, then <main> wrapping both the breadcrumb nav and the content
// block in one shared container, then footer), so this is reusable rather
// than page-specific.
async function captureMainContent(page, outPath) {
  const breadcrumb = page.locator('nav[aria-label="breadcrumb"]');
  // Clips to the breadcrumb nav's own sibling container (the <div
  // class="container"> that holds both the breadcrumb and the content
  // block, per base.html), not to the footer -- <main> itself has
  // flex-grow-1 (a sticky-footer layout), so on a page shorter than the
  // viewport its footer sits at the bottom of the *viewport*, not right
  // after the real content. Clipping to the footer's own top produced a
  // correct-looking crop with several hundred pixels of blank space below
  // the real content, reproduced consistently, not a one-off. The
  // `.container` div isn't flex-stretched the way <main> is, so its own
  // bottom edge reflects where the real content actually ends.
  const container = page.locator('main .container').first();
  const breadcrumbBox = await breadcrumb.boundingBox();
  const containerBox = await container.boundingBox();
  const top = breadcrumbBox.y + breadcrumbBox.height;
  await page.screenshot({
    path: outPath,
    clip: {
      x: 0,
      y: top,
      width: VIEWPORT.width,
      height: containerBox.y + containerBox.height - top,
    },
  });
}

// Crops the resources page to just its own main content and the first
// `tileCount` resource cards (`.resource-card`, resources/resource_card.html)
// -- there are well over ten resources on this seed (see the manifest
// entry's own description), more than a screenshot needs to show at once.
// Same breadcrumb-based top edge as captureMainContent, but the bottom edge
// is the Nth tile's own bottom (plus a little breathing room) instead of
// the container's, which would show every resource.
async function captureResourceTiles(page, outPath, tileCount) {
  const breadcrumb = page.locator('nav[aria-label="breadcrumb"]');
  const breadcrumbBox = await breadcrumb.boundingBox();
  const top = breadcrumbBox.y + breadcrumbBox.height;
  const lastTile = page.locator('.resource-card').nth(tileCount - 1);
  const lastTileBox = await lastTile.boundingBox();
  const bottomPad = 24;
  await page.screenshot({
    path: outPath,
    clip: {
      x: 0,
      y: top,
      width: VIEWPORT.width,
      height: lastTileBox.y + lastTileBox.height - top + bottomPad,
    },
  });
}

const ABOUT_HEADING_TEXT = 'About Mathematics Teachers Association';
const ABOUT_LEAD_TEXT =
  'Supporting maths educators across Aotearoa with resources, professional development, and community.';
const ABOUT_BODY_TEXT =
  "Founded by working teachers, Mathematics Teachers Association connects members through events, a shared resource library, and a members' forum — helping every classroom benefit from what the whole community already knows.";

// heading_block is a plain CharBlock (StructBlock field "Heading text*"),
// not Draftail -- fill() works directly, the same reasoning
// fillTitleBlockText (shared/browser-helpers.mjs) already documents for
// HomePage's own TypographyBlock. Size is a required select with no
// pre-selected default ("Select a heading size" is a placeholder, not a
// real choice), so it must be set explicitly or the block is invalid.
async function fillHeadingBlockText(page, text) {
  // .last() -- this is always the most recently inserted block, the same
  // "target the last match" reasoning fillBodyText (shared/browser-
  // helpers.mjs) already uses, needed here too once a page has more than
  // one heading_block on it.
  await page.getByRole('textbox', { name: 'Heading text*' }).last().fill(text);
  await page.getByRole('combobox', { name: 'Size*' }).last().selectOption('H2');
}

// About starts as an empty page (create_sample_cms_content creates it with
// body=[]), a child of Home -- resolved by link text off the page explorer,
// the same runtime-lookup pattern getEnglishHomePageId already establishes,
// rather than a hard-coded ID.
async function getAboutPageId(page, homeId) {
  await page.goto(`${BASE_URL}/cms/pages/${homeId}/`);
  await page.waitForLoadState('networkidle');
  const link = page.getByRole('link', { name: 'About', exact: true });
  const href = await link.getAttribute('href');
  return href.match(/\/pages\/(\d+)\//)[1];
}

// Removes "Articles" entirely, once, before any theme's own capture --
// every navbar in this composite wants it gone, so unlike the per-theme
// label differences below, this is a permanent, one-time edit rather than
// something reapplied per theme. A real deletion of that menu item
// (wagtailmenus' own inline-formset "Delete" button, applied on Save) --
// only the menu item goes, not the Articles index page itself.
// Targets the menu item by position, not by filtering for its linked
// page's name -- found live that every item's region matches a `hasText`
// filter for any linked page's name (the chooser widget's own template
// text repeats every choosable page name somewhere in each item's own
// markup, not just the one item actually pointing to it), so
// `getByRole("region").filter({ hasText: "Articles" })` resolved to all 5
// items, not 1, and failed Playwright's strict mode rather than silently
// picking the wrong one. Position is reliable here specifically because
// create_sample_cms_content (via seed-marketing.sh) always creates these
// five items in the same fixed order (About, Events, Resources, Members
// Only, Articles) -- see its own _create_menus method.
async function deleteArticlesMenuItem(page) {
  await page.goto(`${BASE_URL}/cms/wagtailmenus/mainmenu/`);
  await page.waitForLoadState('networkidle');
  await page
    .getByRole('region', { name: 'Menu item 5' })
    .getByRole('button', { name: 'Delete' })
    .click();
  await page.getByRole('button', { name: 'Save' }).click();
  await page.waitForLoadState('networkidle');
}

// Sets the main menu's own per-theme text -- About/Events' "Link text"
// overrides (blank falls back to the linked page's own title, "About"/
// "Events") and the 4th item's label (the "Members Only" page, relabelled
// "Forum"/"Community" depending on the theme, same override mechanism).
// Always written, even to "" for themes that don't want an override, for
// the same reseed/re-run-safety reason applyNavbarTheme always writes
// custom_css -- otherwise a later theme's label could bleed into an
// earlier one on a re-run without reseeding.
// Position-based for the same reason deleteArticlesMenuItem is (see its
// own comment) -- Menu item 1 is About, Menu item 2 is Events, Menu item 4
// is the Members Only-linked item (Menu item 3, Resources, is never
// relabelled by any theme, only sometimes hidden -- see
// captureNavbarCrop).
// Fills one field and waits for its real DOM value to match, rather than
// trusting fill() and moving straight on to the next field -- found live,
// building this function: three fill() calls in a row followed by one Save
// worked every time tested interactively, but the real headless
// docs:screenshots run intermittently saved stale values for one or more
// of the three fields (the same interactive-vs-headless gap
// docs-conventions.md bullet 18 already warns about). Each field is a
// plain text input, not Draftail, so this isn't bullet 11's debounce race
// -- but verifying the real value before moving on is the same "wait for a
// real end state" fix in spirit, and resolved it.
// Uses real keystrokes (pressSequentially), not fill() -- found live that
async function fillAndVerify(locator, value) {
  await locator.fill(value);
  const handle = await locator.elementHandle();
  await locator
    .page()
    .waitForFunction(
      ([el, expected]) => el.value === expected,
      [handle, value]
    );
}

// Reads the three fields' real saved values straight from a fresh page
// load's DOM, bypassing getByRole/getByLabel entirely -- used to confirm a
// save actually landed as expected, deliberately not sharing machinery
// with the edit step it's checking.
async function readMainMenuLabels(page) {
  await page.goto(`${BASE_URL}/cms/wagtailmenus/mainmenu/`);
  await page.waitForLoadState('networkidle');
  return page.evaluate(() => ({
    about: document.querySelector('[name="menu_items-0-link_text"]')?.value,
    events: document.querySelector('[name="menu_items-1-link_text"]')?.value,
    item4: document.querySelector('[name="menu_items-3-link_text"]')?.value,
  }));
}

// "Events" (Menu item 2) is a custom-URL link, not an internal page link --
// unlike About/Members Only (real Wagtail pages, where a blank Link text
// falls back to the page's own title), a custom-URL item's Link text is
// the *only* source of its label, and wagtailmenus' own server-side
// validation rejects saving it blank. Found the hard way: submitting
// events='' didn't just leave that one field unchanged, it silently failed
// the *entire* form (all three fields reverted to whatever they were
// before, not just this one) -- confirmed by comparing the values actually
// sent right before clicking Save (logged, and correct) against what a
// fresh reload showed afterwards (still the previous save's values). This
// default is the literal text create_sample_cms_content seeds ("Events"),
// used whenever a theme doesn't want to override it, so "no override"
// means "explicitly the real default," never blank.
const DEFAULT_EVENTS_LABEL = 'Events';

async function setMainMenuLabels(
  page,
  { about = '', events = DEFAULT_EVENTS_LABEL, item4 = '' } = {}
) {
  await page.goto(`${BASE_URL}/cms/wagtailmenus/mainmenu/`);
  await page.waitForLoadState('networkidle');
  await fillAndVerify(
    page.getByRole('region', { name: 'Menu item 1' }).getByLabel('Link text'),
    about
  );
  await fillAndVerify(
    page.getByRole('region', { name: 'Menu item 2' }).getByLabel('Link text'),
    events
  );
  await fillAndVerify(
    page.getByRole('region', { name: 'Menu item 4' }).getByLabel('Link text'),
    item4
  );
  await page.getByRole('button', { name: 'Save' }).click();
  await page.waitForLoadState('networkidle');

  const actual = await readMainMenuLabels(page);
  const target = { about, events, item4 };
  if (
    actual.about !== target.about ||
    actual.events !== target.events ||
    actual.item4 !== target.item4
  ) {
    throw new Error(
      `setMainMenuLabels: menu labels did not save as expected (wanted ${JSON.stringify(target)}, got ${JSON.stringify(actual)})`
    );
  }
}

// Three deliberately clashing navbar styles -- background hue, light/dark
// text mode, font stack, and a different fictional association per navbar
// -- so the composite reads as "this is themeable," not as three near-
// identical screenshots. `signInText`/`signUpText` use a real setting
// (AssociationSettings.navbar_signin_label/navbar_signup_label, found
// reading header_desktop.html), not a capture-only trick.
//
// `menuLabels`/`hideNavItemIndices`/`hideLanguagePicker` give each navbar
// its own menu, even though there's only one real MainMenu record behind
// all three -- see setMainMenuLabels and captureNavbarCrop's own comments.
// `hideNavItemIndices` are positions within `.navbar-nav`'s own top-level
// items (0 About, 1 Events, 2 Resources, 3 the Members Only-linked item),
// not deletions -- unlike Articles (deleteArticlesMenuItem), which every
// theme wants gone and so is removed for real, once, these differ per
// theme (Resources absent only for the third, the 4th item absent only for
// the second) in a way a single shared menu record can't represent
// permanently without one theme's requirement undoing another's.
const NAVBAR_THEMES = [
  {
    orgName: 'Wellington Language Academy',
    navbarBg: '#0f9d8c',
    navbarMode: 'dark',
    primary: '#0f9d8c',
    font: '"Playfair Display", serif',
    logoFixture: NAVBAR_1_LOGO_FIXTURE,
    logoTitle: 'Wellington Language Academy logo',
    menuLabels: { item4: 'Forum' },
  },
  {
    orgName: '🛠️ IRONCLAD TRADES GUILD',
    navbarBg: '#14142b',
    navbarMode: 'dark',
    primary: '#d4af37',
    font: '"Poppins", sans-serif',
    menuLabels: { about: 'About Us', events: 'Meetups' },
    hideNavItemIndices: [3],
    customCss: `
      .navbar .nav-link, #sign-up-link {
        text-transform: uppercase;
        white-space: nowrap;
      }
      .navbar-brand {
        font-weight: 900;
      }
    `,
    hideLanguagePicker: true,
  },
  {
    orgName: 'Sunrise Wellness',
    navbarBg: '#ffd9b3',
    navbarMode: 'light',
    primary: '#c0392b',
    font: '"Fredoka", sans-serif',
    logoFixture: NAVBAR_3_LOGO_FIXTURE,
    logoTitle: 'Sunrise Wellness logo',
    menuLabels: { item4: 'Community' },
    hideNavItemIndices: [2],
    customCss: `
      .navbar {
        background: linear-gradient(120deg, #fff6ea 0%, #ffd9b3 100%) !important;
      }
      .navbar-brand {
        transform: scale(1.7);
      }
    `,
    signInText: 'Log In',
    signUpText: 'Join Now',
  },
];

// Opens the association logo chooser and uploads the given fixture --
// generalised from branding-theme.mjs's uploadDemoLogo (tutorial-specific,
// always the same fixture/title) to take both as arguments, since this
// suite's own three navbars need at most one logo, not the same one.
// The chooser's "empty" state (a plain "Choose an image" button, matched by
// its data-chooser-action-choose attribute) only exists before any image
// has ever been chosen. Once one has (every theme after the first, in this
// suite's own run), the widget instead shows the chosen image's title and
// an "Actions" menu -- "Change image" (opens the same picker modal),
// "Edit this image", "Clear choice" -- found live, after the plain
// "Choose an image" locator started timing out (never visible) on this
// suite's second and third logo uploads in the same run.
async function openLogoChooser(page) {
  const chooseButton = page.locator(
    '#id_association_logo-chooser [data-chooser-action-choose]'
  );
  if (await chooseButton.isVisible().catch(() => false)) {
    await chooseButton.click();
    return;
  }
  await page
    .locator('#id_association_logo-chooser')
    .getByRole('button', { name: 'Actions' })
    .click();
  await page.getByRole('button', { name: 'Change image' }).click();
}

async function uploadAssociationLogo(page, fixturePath, title) {
  await openLogoChooser(page);
  const modal = page.locator('[role="dialog"][aria-hidden="false"]');
  await modal
    .getByRole('tab', { name: 'Search' })
    .waitFor({ state: 'visible' });
  await modal.getByRole('tab', { name: 'Upload' }).click();
  await modal
    .locator('#id_image-chooser-upload-title')
    .waitFor({ state: 'visible' });
  await modal.locator('#id_image-chooser-upload-title').fill(title);
  await modal
    .locator('#id_image-chooser-upload-file')
    .setInputFiles(fixturePath);
  await modal.getByRole('button', { name: 'Upload' }).click();
  const useNewImage = modal.getByRole('link', { name: 'Use new image' });
  const isDuplicate = await useNewImage
    .waitFor({ state: 'visible', timeout: 3000 })
    .then(() => true)
    .catch(() => false);
  if (isDuplicate) {
    await useNewImage.click();
  }
  await page.waitForFunction(
    (t) =>
      document
        .querySelector('#id_association_logo-title')
        ?.textContent.trim() === t,
    title
  );
}

// Sets this navbar's own fictional association name and, only for the one
// theme that wants it, its logo. `navbar_logo_or_name.html` shows the logo
// *instead of* the name once "Use logo in navbar" is on (confirmed live,
// not assumed) -- explicitly unchecking it for every theme that doesn't
// want a logo matters, not just leaving it alone, since a logo uploaded for
// an earlier theme in this same run would otherwise keep showing for the
// later ones too.
async function setAssociationBranding(page, theme) {
  await page.goto(`${BASE_URL}/cms/settings/cms/associationsettings/`);
  await page.waitForLoadState('networkidle');
  await page.locator('#id_association_short_name').fill(theme.orgName);
  await page.locator('#id_association_long_name').fill(theme.orgName);
  if (theme.logoFixture) {
    await uploadAssociationLogo(page, theme.logoFixture, theme.logoTitle);
    await page.getByRole('checkbox', { name: 'Use logo in navbar' }).check();
  } else {
    await page.getByRole('checkbox', { name: 'Use logo in navbar' }).uncheck();
  }
  // Real settings (AssociationSettings.navbar_signin_label/
  // navbar_signup_label, found reading header_desktop.html), not a
  // capture-only DOM hack -- always written, even to "" for themes that
  // don't want an override, for the same reseed/re-run-safety reason
  // applyNavbarTheme always writes custom_css.
  await page.locator('#id_navbar_signin_label').fill(theme.signInText ?? '');
  await page.locator('#id_navbar_signup_label').fill(theme.signUpText ?? '');
  await page.getByRole('button', { name: 'Save' }).click();
  await page.waitForLoadState('networkidle');
}

async function applyNavbarTheme(page, theme) {
  await page.goto(`${BASE_URL}/cms/settings/cms/themesettings/`);
  await page.waitForLoadState('networkidle');
  const navbarBgField = page.getByRole('textbox', {
    name: 'Navbar background color*',
    exact: true,
  });
  await navbarBgField.fill(theme.navbarBg);
  await navbarBgField.dispatchEvent('change');
  await page.locator('#id_navbar_colour_mode').selectOption(theme.navbarMode);
  const primaryField = page.getByRole('textbox', {
    name: 'Primary*',
    exact: true,
  });
  await primaryField.fill(theme.primary);
  await primaryField.dispatchEvent('change');
  const fontField = page.getByRole('textbox', {
    name: 'Sans-serif font stack*',
    exact: true,
  });
  await fontField.fill(theme.font);
  await fontField.dispatchEvent('change');
  // Custom CSS Overrides is a real ThemeSettings field (`custom_css`,
  // injected into every page), not a capture-only trick -- it starts
  // collapsed (Meta.classname="collapsed" in ams/cms/models/theme.py), so
  // clicking its heading to expand it is needed before the textarea beneath
  // is fillable. Always written, even to "" for the two themes that don't
  // want it -- otherwise a re-run of this step without reseeding in between
  // would leave the third theme's custom CSS bleeding into the first two.
  await page
    .getByRole('heading', { name: '⚠️ Advanced: Custom CSS Overrides' })
    .click();
  await page.locator('#id_custom_css').fill(theme.customCss ?? '');
  await page.getByRole('button', { name: 'Save' }).click();
  await page.waitForLoadState('networkidle');
}

// Captures on a separate, signed-out browser context/page, not the
// authenticated `page` used to make the settings changes above -- the
// brief wants a visitor's own signed-out view (Sign In/Sign Up links), not
// the admin's avatar menu. Reusing the same authenticated `page` would show
// the wrong state entirely, not just a cosmetic difference.
// Hides this theme's own unwanted nav items/language picker on the
// rendered page itself, right before the crop -- there's no per-theme menu
// in the real product (see NAVBAR_THEMES' own comment), so this is a
// deliberate capture-only visual arrangement, not a hidden bug workaround
// like the other capture-only cases this suite documents elsewhere.
// `hideNavItemIndices` are positions within `.navbar-nav`'s own top-level
// `<li>`s (see NAVBAR_THEMES), found reliable the same way
// deleteArticlesMenuItem/setMainMenuLabels already rely on position over
// text matching. The language picker (`includes/language_dropdown.html`)
// has a stable accessible name ("Toggle language", its own aria-label)
// regardless of position, so that one's found by role instead.
async function captureNavbarCrop(anonPage, theme) {
  await anonPage.goto(`${BASE_URL}/en/`);
  await anonPage.waitForLoadState('networkidle');
  await prepareForCapture(anonPage);
  await anonPage.evaluate((hideNavItemIndices) => {
    const items = document.querySelectorAll('.navbar-nav > li.nav-item');
    (hideNavItemIndices ?? []).forEach((i) => {
      if (items[i]) items[i].style.display = 'none';
    });
  }, theme.hideNavItemIndices);
  if (theme.hideLanguagePicker) {
    // A <style> tag with !important (prepareForCapture's own established
    // approach for hiding nondeterministic/unwanted chrome), not a direct
    // inline style mutation -- found live that setting
    // element.style.display via evaluate() didn't stick for this specific
    // element, consistently, only in the real headless docs:screenshots
    // run (confirmed correct, every time, when tested interactively
    // instead). Not root-caused; a style tag is also just as suited to the
    // job as a direct mutation, so this is the fix rather than a workaround
    // for a workaround.
    await anonPage.addStyleTag({
      content: 'a[aria-label="Toggle language"] { display: none !important; }',
    });
  }
  const nav = anonPage.locator('nav.navbar').first();
  const box = await nav.boundingBox();
  const buffer = await anonPage.screenshot({ clip: box });
  return { buffer, width: box.width, height: box.height };
}

export const steps = {
  // Sets the demo organisation name (once, for every later marketing
  // capture in this run) and creates three branded membership options --
  // the marketing seed's own sample_data doesn't cover either, and using
  // sample_data's own "Sample Individual Membership - 1 Month" naming would
  // read as dev fixture data in a marketing screenshot.
  async marketingMembershipManagement(page, outPath) {
    await login(page);
    await setAssociationName(page);
    for (const option of MEMBERSHIP_OPTIONS) {
      await createMembershipOption(page, option);
    }
    await page.setViewportSize({ width: VIEWPORT.width, height: 1400 });
    await page.goto(`${BASE_URL}/en/users/memberships/apply-individual/`);
    await page.waitForLoadState('networkidle');
    await prepareForCapture(page);
    // topPad: 0 -- the breadcrumb ("Home / Admin Account / Apply for
    // Membership") sits close enough above this page's own H1 that the
    // default 24px padding still let a sliver of it into frame.
    await clipBetween(
      page,
      outPath,
      page.getByRole('heading', { name: 'Apply for Membership', exact: true }),
      page.getByRole('button', { name: 'Register membership' }),
      { topPad: 0 }
    );
    return true;
  },

  // Relies on docs/screenshots/fixtures/marketing_billing_history.py having
  // already run (see seed-marketing.sh) to create the admin's three-period
  // membership/invoice history before this step ever opens the browser.
  async marketingIntegratedBilling(page, outPath) {
    await login(page);
    await page.setViewportSize({ width: VIEWPORT.width, height: 1400 });
    await page.goto(`${BASE_URL}/en/users/~redirect/`);
    await page.waitForLoadState('networkidle');
    await prepareForCapture(page);
    const heading = page.getByRole('heading', {
      name: 'Memberships',
      exact: true,
    });
    const table = page
      .locator('table')
      .filter({ hasText: 'Standard membership' })
      .first();
    await clipBetween(page, outPath, heading, table);
    return true;
  },

  // Shows real About-page content, not Home's example/showcase blocks --
  // create_sample_cms_content creates About empty (body=[]), so this fills
  // it with three genuine blocks (Heading, Lead paragraph, Paragraph)
  // rather than reusing Home's "this is a sample/test website" copy. Note
  // heading_block/lead_paragraph_block/paragraph_block are all available on
  // ContentPage (unlike title_block, which is HomePage-only and isn't
  // offered here at all -- found live, "Insert a block" has no such option
  // on this page type). Each block is saved on its own, reopening the edit
  // page fresh before the next insert -- the same defensive pattern
  // docs-conventions.md bullet 15 establishes for Home's Title block (whose
  // widgets can clobber a still-unsaved sibling edit); not confirmed to
  // apply to heading_block specifically, but cheap enough to do anyway.
  async marketingContentManagementSystem(page) {
    await login(page);
    const homeId = await getEnglishHomePageId(page);
    const aboutId = await getAboutPageId(page, homeId);
    const openAboutEdit = async () => {
      await page.goto(`${BASE_URL}/cms/pages/${aboutId}/edit/`);
      await page.waitForLoadState('networkidle');
    };

    await openAboutEdit();
    await insertBodyBlock(page, 'Heading block');
    await fillHeadingBlockText(page, ABOUT_HEADING_TEXT);
    await saveDraft(page);

    await openAboutEdit();
    await insertBodyBlock(page, 'Lead paragraph block');
    // A short, explicit settle before typing -- found only in the real
    // headless docs:screenshots run, never interactively (the same
    // interactive-vs-headless gap docs-conventions.md bullet 18 already
    // warns about): fillBodyText's own keystrokes landed too early for a
    // Draftail editor mounted immediately beforehand by insertBodyBlock,
    // silently discarded rather than delayed, so even fillBodyText's own
    // "wait for the hidden input to update" check timed out with nothing to
    // find. No better real-state signal was found for "this specific
    // Draftail instance has finished mounting."
    await page.waitForTimeout(500);
    await fillBodyText(page, ABOUT_LEAD_TEXT);
    await saveDraft(page);

    await openAboutEdit();
    await insertBodyBlock(page, 'Paragraph block');
    await page.waitForTimeout(500);
    await fillBodyText(page, ABOUT_BODY_TEXT);
    await saveDraft(page);

    await openAboutEdit();
    // Body's own region scrolled to the top of the viewport puts
    // Title/Visibility/Is structure only (ams/cms/models/pages.py's
    // content_panels list, all above Body) out of frame on its own.
    await page.getByRole('region', { name: 'Body' }).scrollIntoViewIfNeeded();
    await prepareForCapture(page);
  },

  // This Discourse instance requires SSO sign-in to view anything at all --
  // found live, the hard way: navigating here signed out doesn't show a
  // public homepage, it redirects straight to AMS's own sign-in page (the
  // same page forum.mjs's own forumSignInPrompt step screenshots
  // deliberately). So, like every other forum step in this suite,
  // login() plus the `/forum/` SSO entry point is required, not optional --
  // this accepts the admin's own personalised "Welcome back" chrome rather
  // than a truly anonymous view, the same trade-off forumHome (forum.mjs)
  // already makes. Relies on
  // docs/screenshots/fixtures/marketing_forum_content.rb having already run
  // (via seed-marketing.sh) to create the demo users/topics/replies this
  // screenshot shows.
  async marketingCommunityForum(page) {
    await login(page);
    await page.goto(`${BASE_URL}/forum/`);
    await page.waitForLoadState('load');
  },

  // Signed out, like the forum above -- a visitor deciding whether to
  // attend rather than the admin managing the listing. Cropped to just the
  // page's own main content (captureMainContent), excluding header,
  // breadcrumbs, and footer. Relies on seed-marketing.sh having run
  // create_sample_events, which spreads its ~25 events across several NZ
  // regions (Auckland/Wellington/Christchurch/Dunedin/Rotorua/Queenstown)
  // specifically so they render as separate map pins/clusters instead of
  // one pin repeated in the same city (see
  // ams/events/management/commands/create_sample_events.py).
  async marketingEvents(page, outPath) {
    await page.setViewportSize({ width: VIEWPORT.width, height: 1400 });
    await page.goto(`${BASE_URL}/en/events/`);
    await page.waitForLoadState('networkidle');
    await prepareForCapture(page);
    await captureMainContent(page, outPath);
    return true;
  },

  // Signed out, same reasoning as Events above. Relies on seed-marketing.sh
  // having run create_sample_resources (well over 30 resources, comfortably
  // past the "at least ten" this screenshot needs) -- cropped to just the
  // first 4 resource cards (captureResourceTiles) rather than the whole
  // list, which would run the image on for many screens.
  async marketingResources(page, outPath) {
    await page.setViewportSize({ width: VIEWPORT.width, height: 1400 });
    await page.goto(`${BASE_URL}/en/resources/`);
    await page.waitForLoadState('networkidle');
    await prepareForCapture(page);
    await captureResourceTiles(page, outPath, 4);
    return true;
  },

  // Builds one composite image from three separately-themed navbar crops,
  // rather than three manifest entries -- the brief asks for one stacked
  // image, not three. No new dependency: three PNG buffers are base64-
  // inlined into a tiny local page (page.setContent(), not page.goto(), so
  // no file:// path resolution is needed) laid out as a plain vertical
  // stack, then that page itself is screenshotted as the real output.
  // Each navbar now gets its own fictional association name, its own menu
  // labels/visible items (see NAVBAR_THEMES' own comment), and fully
  // different theme settings, so the composite reads as three different
  // clients' sites rather than one site re-coloured three times. Depends on
  // marketingMembershipManagement (earlier in manifest.json) having set the
  // demo organisation name back to Mathematics Teachers Association for its
  // own screenshot, and create_sample_cms_content (via seed-marketing.sh)
  // having already populated the main menu -- this step removes "Articles"
  // once, before looping over the three themes (every theme wants it gone,
  // so it's a real, permanent deletion rather than a per-capture hide), and
  // leaves the association name/theme/menu labels set to the last theme's
  // values afterwards (harmless: nothing later in the marketing set depends
  // on branding).
  async marketingCustomizationAndBranding(page, outPath) {
    await login(page);
    await deleteArticlesMenuItem(page);

    const anonContext = await page.context().browser().newContext({
      viewport: VIEWPORT,
      deviceScaleFactor: DEVICE_SCALE_FACTOR,
    });
    const anonPage = await anonContext.newPage();
    // Needed for any theme's uploaded logo to render at all -- this fresh
    // context has no route registered otherwise, unlike the authenticated
    // `page` (which run.mjs's own main() loop sets up), and an uploaded
    // image's URL is only reachable from inside the node container via this
    // rewrite (see proxyMinioMedia's own comment).
    await proxyMinioMedia(anonPage);

    const crops = [];
    for (const theme of NAVBAR_THEMES) {
      await setAssociationBranding(page, theme);
      await applyNavbarTheme(page, theme);
      await setMainMenuLabels(page, theme.menuLabels);
      crops.push(await captureNavbarCrop(anonPage, theme));
    }
    await anonContext.close();

    const images = crops
      .map(
        (crop) =>
          `<img src="data:image/png;base64,${crop.buffer.toString('base64')}" width="${crop.width}" height="${crop.height}">`
      )
      .join('');
    const totalHeight = crops.reduce((sum, crop) => sum + crop.height, 0);
    await page.setContent(
      `<style>body{margin:0;}img{display:block;}</style>${images}`
    );
    // Sized to the crops' own known total height, not measured/assumed --
    // relying on the browser to infer each <img>'s "natural" size from a
    // base64-embedded PNG's own pixel dimensions (already 2x the CSS size,
    // from this suite's device scale factor) produced a composite several
    // times taller than the real content in an earlier version of this
    // step; explicit width/height attributes on each <img> avoid that.
    await page.setViewportSize({
      width: VIEWPORT.width,
      height: Math.ceil(totalHeight),
    });
    const buffer = await page.screenshot();
    fs.writeFileSync(outPath, buffer);
    return true;
  },
};
