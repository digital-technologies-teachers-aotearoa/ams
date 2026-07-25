// Orientation (tutorial 1). Every step here is read-only, so unlike later
// tutorials it doesn't matter what order these run in, or whether the site
// has been freshly seeded.

import { BASE_URL } from "../shared/config.mjs";
import { login } from "../shared/browser-helpers.mjs";

export const steps = {
  async orientationSignIn(page) {
    await page.goto(`${BASE_URL}/en/accounts/login/`);
    await page.waitForLoadState("networkidle");
  },

  async orientationYourAccount(page) {
    await login(page);
  },

  async orientationCmsDashboard(page) {
    await login(page);
    await page.goto(`${BASE_URL}/cms/`);
    await page.waitForLoadState("networkidle");
  },

  async orientationDjangoAdmin(page) {
    await login(page);
    await page.goto(`${BASE_URL}/admin/`);
    await page.waitForLoadState("networkidle");
  },
};
