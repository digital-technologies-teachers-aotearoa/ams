// Two example screenshots that prove the pipeline end to end (embedded in
// docs-conventions.md itself, not a tutorial). Tutorial tasks (T13 onward)
// add their own steps for the screens they document, rather than reusing
// these.

import { BASE_URL } from "../shared/config.mjs";
import { login } from "../shared/browser-helpers.mjs";

export const steps = {
  async exampleLogin(page) {
    await page.goto(`${BASE_URL}/en/accounts/login/`);
    await page.waitForLoadState("networkidle");
  },

  async exampleDashboard(page) {
    await login(page);
    await page.goto(`${BASE_URL}/cms/`);
    await page.waitForLoadState("networkidle");
  },
};
