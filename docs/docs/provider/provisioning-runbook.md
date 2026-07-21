# Provisioning runbook

**Who this page is for:** the provider standing up a new client instance.
Technical audience; terse runbook register — see [Documentation conventions](../developer/docs-conventions.md#style-rules-for-client-facing-pages).

This runbook is deliberately opinionated about the provider's actual stack: DigitalOcean App Platform, Postmark, Discourse, Xero.
For platform-agnostic deployment concepts (container requirements, the full environment variable reference, `deploy_steps`) that apply to any AMS installation, see [Deployment](../developer/deployment.md) — this page covers only the DigitalOcean-specific and questionnaire-driven parts, cross-linking there for everything generic rather than duplicating it.

Follow the phases below in order.
Each one assumes the previous phase is complete.

## 1. Prerequisites

Confirm all of the following have come back from the client before starting:

- Completed [decision questionnaire](../getting-started/decision-questionnaire.md).
- Reviewed [costs sheet](../getting-started/costs-sheet.md) (no action here, just confirms the client has seen it).
- Access granted per the [accounts & access checklist](../getting-started/accounts-checklist.md):
    - Postmark — invited as a **Technical** team member.
    - Domain registrar (Cloudflare) — invited with the **Domain DNS** role.
    - DigitalOcean — invited to the client's **Team**.
    - Xero (only if enabled) — the authorising user's name and email, not yet connected (that happens in §7).
    - Discourse (only if enabled) — the client creates the production forum themselves, whenever they're ready (accounts checklist); nothing for the provider to prepare first, so this can already be done by the time you reach §6.
      The UAT forum needs no client action at all — it's self-hosted by the provider (§6).
- Domain purchased and owned by the client's own account, not a volunteer's personal one (questionnaire Q1).

## 2. Server setup (DigitalOcean App Platform)

Provision each client with their own small GitOps repository, following the pattern already live in [`dtta-website`](https://github.com/digital-technologies-teachers-aotearoa/dtta-website) — a real second AMS deployment, not a hypothetical:

- `environments/uat/` and `environments/prod/`, each with an `app.yml` (the DigitalOcean App Platform spec) and a `config.yml` (the AMS image version plus the questionnaire-driven `AMS_*` values from §4 — kept separate from `app.yml` so a version bump or a settings change is a small, reviewable diff).
- A GitHub Actions workflow per environment (`deploy-uat.yml`, `deploy-prod.yml`), triggered on push to that environment's path, deploying via `digitalocean/app_action/deploy@v2` with `project_id` and `app_spec_location` pointing at that environment's files.
- Secrets (`DJANGO_SECRET_KEY`, storage keys, `XERO_*`, etc.) stored in a GitHub Environment per deployment target and injected as `env:` on the deploy step — never committed to the repo.

The AMS project's own `.do/app.yaml` (see [AMS project development site](../developer/project-dev-site.md)) is a second, simpler working example of the same App Platform spec syntax (job/component structure, instance sizing) — useful as a syntax reference, but `dtta-website`'s split-by-environment repo is the structure to actually follow for a client.

None of this needs to be written by hand up front.
For the initial stand-up, it's fine (and often easier) to create each app through DigitalOcean's own web console — this is also the simplest way to attach UAT's database: the console's database-creation step offers **Dev Database** as a plain option, rather than requiring you to already know that a bare `engine: PG` entry with no `cluster_name` is what produces one in the YAML (§5).
Once an app exists and runs correctly, export its spec (the App Platform console's **App Spec** tab, or `doctl apps spec get`) into the client's `environments/<env>/app.yml` to bring it under the GitOps flow above — the console and the YAML describe the same underlying app either way, so adopting one after the other doesn't require re-provisioning anything.

Clone `dtta-website`'s structure for the new client's own repo, then per environment (whether you're about to create each app through the console or write its spec directly):

1. Create the client's DigitalOcean project and one App Platform app per environment (UAT, production) under their team.
2. Add each environment's database — see §5 for why UAT's differs from production's.
3. Add the `django` web component from the [`ams-django` GHCR image](https://github.com/digital-technologies-teachers-aotearoa/ams/pkgs/container/ams-django), pinned to a specific released tag/digest — not a floating `latest` — so the client's site doesn't move underneath them on an unrelated AMS release.
   `http_port: 5000`, `run_command: /start-web.sh`, instance size `apps-s-1vcpu-0.5gb` (512MB) to start.
   This component runs gunicorn only — there's no separate worker process to size or split out — see [Deployment](../developer/deployment.md#container-resources) for sizing up to `apps-s-1vcpu-1gb` when traffic justifies it.
4. Add a `job-deploy` **PRE_DEPLOY** job on each environment: `run_command: python /app/manage.py deploy_steps`, instance size `apps-s-1vcpu-1gb-fixed` (extra headroom, since migrations can spike memory; runs once per deploy then stops).
5. If the client chose Xero billing (questionnaire Q5), add a `fetch-invoice-updates` **SCHEDULED** job on each environment, same image: `run_command: python /app/manage.py fetch_invoice_updates`, cron `*/15 * * * *` — this is the fallback for any webhook Xero fails to deliver (see §7).
6. Set ingress: route `/` to the `django` component.
7. Create two Spaces buckets per environment (public and private media) in the region chosen at questionnaire Q6.
   DigitalOcean Spaces endpoints follow `https://<region>.digitaloceanspaces.com`, e.g. `https://syd1.digitaloceanspaces.com` for Sydney — match the region to Q6's answer.
   See [Deployment](../developer/deployment.md#requirements) for the full set of `DJANGO_MEDIA_PUBLIC_*` / `DJANGO_MEDIA_PRIVATE_*` variables each bucket needs.
8. Don't attach the client's real domain to the production app yet — that's the cutover phase (§8).
   Use DigitalOcean's assigned `*.ondigitalocean.app` hostname for both environments until then.

## 3. Postmark domain & DNS configuration

Assumes the client has already created their Postmark account and invited the provider as a **Technical** team member (accounts checklist).

1. Sign in to the client's Postmark account.
2. Open (or create) the Server the client's site will send from, and copy its **Server API Token** — this becomes `POSTMARK_SERVER_TOKEN`.
3. Go to **Sender Signatures** → **Add Domain or Signature** → **Add Domain** → enter the client's domain → **Verify Domain**.
4. Postmark generates a DKIM record (and an optional Return-Path record).
   Only the DKIM record is required to verify the domain.
5. Add the DKIM record as a **TXT** record in the client's DNS (Cloudflare, via the Domain DNS access from the accounts checklist), using the exact Host and Value Postmark shows.
6. Click **Verify** in the DKIM row.
   Propagation can take up to 48 hours, so start this step early rather than on cutover day.
7. Optional, for better deliverability: add the Return-Path CNAME record too, and set up DMARC (Postmark's Authentication page has a "Set up DMARC" section).
   Neither is required for step 6 to pass.

*(Checked against Postmark's own documentation manual, 2026-07.)*

Set `DJANGO_EMAIL_ESP=postmark` and `POSTMARK_SERVER_TOKEN` on the app (§2) once you have the token from step 2 — the domain verification above (steps 3–6) doesn't block setting these, only step 8's cutover does.

## 4. Environment settings

The table below maps every [decision questionnaire](../getting-started/decision-questionnaire.md) answer to where it's actually configured.
Everything else — secrets, database credentials, storage keys, observability (Sentry, Logtail) — isn't a client decision, so it isn't repeated here: see [Deployment](../developer/deployment.md#environment-variables) for the full environment variable reference.

| Questionnaire answer | Decides | Where it's configured |
| --- | --- | --- |
| [Q1: organisation name and domain](../getting-started/decision-questionnaire.md#1-organisation-name-and-domain) | The website's domain | `SITE_DOMAIN` (used by `setup_cms` to create the Site record) |
| | The organisation's displayed name | Not an env var — set via Wagtail admin → Settings → Association after launch (Tutorial 2: Branding & theme), or with a one-off shell update alongside `deploy_steps` |
| [Q2: languages](../getting-started/decision-questionnaire.md#2-languages) | Which languages, and their order | [`AMS_ENABLED_LANGUAGES`](../getting-started/settings-glossary.md#ams_enabled_languages) (comma-separated, primary language first) |
| [Q3: membership model](../getting-started/decision-questionnaire.md#3-membership-model) | Free-membership approval | [`AMS_REQUIRE_FREE_MEMBERSHIP_APPROVAL`](../getting-started/settings-glossary.md#ams_require_free_membership_approval) |
| | Membership types and pricing | Not an env var — created directly in the CMS (Tutorial 6: Memberships) |
| [Q4: staff notification preferences](../getting-started/decision-questionnaire.md#4-staff-notification-preferences) | Membership notifications | [`AMS_NOTIFY_STAFF_MEMBERSHIP_EVENTS`](../getting-started/settings-glossary.md#ams_notify_staff_membership_events) |
| | Organisation notifications | [`AMS_NOTIFY_STAFF_ORGANISATION_EVENTS`](../getting-started/settings-glossary.md#ams_notify_staff_organisation_events) |
| [Q5: optional features](../getting-started/decision-questionnaire.md#5-optional-features) | Events | [`AMS_EVENTS_ENABLED`](../getting-started/settings-glossary.md#ams_events_enabled) |
| | Resources | [`AMS_RESOURCES_ENABLED`](../getting-started/settings-glossary.md#ams_resources_enabled) |
| | Forum | `DISCOURSE_REDIRECT_DOMAIN`, `DISCOURSE_CONNECT_SECRET` — see §6 |
| | Xero billing | `AMS_BILLING_SERVICE_CLASS`, `XERO_*` — see §7 |
| [Q6: data sovereignty / hosting region](../getting-started/decision-questionnaire.md#6-data-sovereignty-hosting-region) | Not a Django setting | DigitalOcean app/database/Spaces region, Postmark account region, Discourse hosting region, log-storage region — all chosen during server setup (§2), not configured via env var |
| [Q7: branding assets](../getting-started/decision-questionnaire.md#7-branding-assets) | Not a provisioning-time setting | Loaded post-launch via Wagtail admin (Tutorial 2: Branding & theme) |
| [Q8: named roles](../getting-started/decision-questionnaire.md#8-named-roles) | Site admin | Create the first account by running `python manage.py createsuperuser` as a one-off command against the deployed app (DigitalOcean App Platform's Console, or `doctl apps console`), using the email named as site admin |
| | DNS controller, credit-card holder | Access only — no Django setting |
| [Q9: reference site](../getting-started/decision-questionnaire.md#9-reference-site-optional) | Not a Django setting | Informational — briefs the provider before building the site, nothing to configure |

## 5. UAT site standup

1. UAT's database is provisioned differently from production's, and this is deliberate, not a shortcut to fix: it's a DigitalOcean App Platform **Dev Database** rather than a full Managed Database — in the console, just pick **Dev Database** when creating UAT's app (the easiest way to get one); in YAML, it's a plain `databases: - engine: PG` entry with no `cluster_name` / `production: true` (see `dtta-website`'s `environments/uat/app.yml`, or export the console-created app's spec per §2).
   Cheaper to run (matches the [costs sheet](../getting-started/costs-sheet.md)'s UAT hosting row), but more limited: you can't create additional schemas or databases on it, and you can't modify its user's permissions — if a client's UAT ever needs either, upgrade it to a Managed Database, the same as production uses.
   Known gotcha: if the *first* deploy to a brand-new Dev Database fails partway through, its user can be left without permission on the `public` schema, and every later deploy fails the same way.
   The fix is DigitalOcean's own: delete the Dev Database, redeploy until the `job-deploy` PRE_DEPLOY step completes successfully end to end, and the database is then usable — don't spend time diagnosing this as an AMS or migration bug first.
2. Otherwise, mirror production's app spec — same image/digest, the same `job-deploy` PRE_DEPLOY step, and `createsuperuser` (§4) run against it once deployed — with Spaces buckets either shared with production or dedicated smaller ones.
3. No production DNS is needed for UAT — DigitalOcean's own generated `*.ondigitalocean.app` hostname is enough for the client to review on.
4. Keep the UAT site running after launch rather than tearing it down — see [glossary: UAT](../getting-started/glossary.md#uat).

## 6. Discourse instance setup & SSO integration

Only if the client chose the forum (questionnaire Q5).
UAT and production forums are set up differently, with different admin-access flows — do both, not just production.

### UAT forum (self-hosted)

Cheap to run (see the [costs sheet](../getting-started/costs-sheet.md)'s UAT forum row) because it's self-hosted rather than a paid Discourse-hosted subscription — but that also makes patching Discourse itself an ongoing provider responsibility, not something covered automatically the way Discourse's own hosting covers it for production.

1. Stand up a self-hosted Discourse instance at a UAT forum subdomain (e.g. `forum-uat.<domain>`) — see [developer/forum.md](../developer/forum.md) for self-hosting links.
2. Because you install it yourself, your own account is the first one created on the instance — you're already an admin, with nothing to request from the client.
3. Configure Discourse's site settings as documented in [admin/forum.md](../admin/forum.md) (the same settings block used for production, below) and set `DISCOURSE_REDIRECT_DOMAIN` / `DISCOURSE_CONNECT_SECRET` on the UAT app.
4. Confirm SSO works against the UAT site.
5. Keep this instance patched going forward — treat it as an ongoing maintenance task for the life of the client's site, not a one-off setup step.

### Production forum (Discourse-hosted)

The client's own paid Discourse Business/Pro subscription (accounts checklist) — Discourse's own hosting, not self-hosted, so patching is Discourse's job here, not the provider's.
There's no "instance the provider stands up first" here at all: the client creates the forum themselves by signing up on Discourse's own site, on a temporary Discourse-assigned subdomain — nothing to wait on from the provider before they do.

1. Once the client has signed up (accounts checklist) and added you as an admin, sign in to their forum.
   Discourse's bootstrap mode made the client's own signup an admin automatically, since theirs was the first account on a brand-new instance — that's why they needed to add you rather than the other way round.
2. Configure Discourse's site settings exactly as documented in [admin/forum.md](../admin/forum.md): `enable_discourse_connect`, `discourse_connect_url` (`<website domain>/forum/sso`), `discourse_connect_secret`, `logout_redirect`, and the accompanying `invite_only` / `login_required` / `allow_new_registrations` / `auth_overrides_*` block — including `bootstrap_mode_min_users: '0'`, which turns bootstrap mode off going forward so no later signup can self-promote to admin the way the client's did in step 1.
3. Point the client's real forum subdomain (e.g. `forum.<domain>`) at the hosted instance, replacing Discourse's temporary one: in the Discourse admin dashboard, **Change Domain Name** → enter the subdomain; add the **CNAME** record it requires (target given in Discourse's welcome email) via the client's DNS (Cloudflare access from the accounts checklist).
   Custom domains need a paid plan (Pro/Business/Enterprise), so do this once the client has moved off any free trial.
4. Set `DISCOURSE_REDIRECT_DOMAIN=https://forum.<domain>` and `DISCOURSE_CONNECT_SECRET` (matching step 2's value) on the production app — a different subdomain and secret from UAT's.
5. Confirm SSO works: sign in to the main site, then visit the forum — you should already be signed in, with no separate forum password.
6. Once the client's subscription is active (and the non-profit discount applied, if requested), remove their temporary personal admin account.
   From here, AMS is the source of truth for forum admin — see [admin/forum.md#admin-sync](../admin/forum.md#admin-sync): superusers get forum admin, everyone else has it revoked, on every SSO login.

## 7. Xero connection

Only if the client chose Xero billing (questionnaire Q5).

Follow [developer/billing.md](../developer/billing.md)'s Custom Connection flow in full — this runbook doesn't duplicate it. In short:

1. Create the Custom Connection in the Xero Developer Portal, naming the client's authorising user (from the accounts checklist) as the person who will authorise it.
2. Once they authorise — and their organisation has an active [Custom Connection subscription](https://connect.xero.com/custom) — retrieve the Client ID, Client Secret, and Tenant ID.
3. Set `AMS_BILLING_SERVICE_CLASS=ams.billing.providers.xero.XeroBillingService`, `XERO_CLIENT_ID`, `XERO_CLIENT_SECRET`, `XERO_TENANT_ID`.
4. Set `XERO_ACCOUNT_CODE`, `XERO_AMOUNT_TYPE`, `XERO_CURRENCY_CODE` from the client's existing Xero chart of accounts and organisation currency — not a decision questionnaire question, since it depends on how the client's own Xero is already set up rather than a website preference.
5. Register the webhook (Xero Developer Portal → app → Webhooks → Delivery URL `https://<domain>/billing/xero/webhooks/`) and set `XERO_WEBHOOK_KEY` to the key Xero generates.
6. Confirm the `fetch-invoice-updates` scheduled job (§2) is present as the fallback for any missed webhook.

**If the client didn't choose Xero billing:** `config/settings/production.py` currently reads all seven `XERO_*` variables with no default, regardless of `AMS_BILLING_SERVICE_CLASS` — so a non-Xero deployment still needs *something* set for each of them today, and no billing-optional deployment path has been established or verified.
Flagged as a follow-up (see this task's completion notes) rather than resolved here.

## 8. Production cutover and DNS

1. Confirm the client has signed off on UAT testing (the [Building your website](../tutorials/index.md) tutorial series covers what they check).
2. Add the client's domain to the production app's domain list and wait for DigitalOcean's managed TLS certificate to issue.
3. In Cloudflare (Domain DNS access from the accounts checklist), add the DNS record pointing the client's domain at the production app's DigitalOcean-assigned hostname.
4. Confirm the Postmark DKIM record is fully verified (§3) *before* cutting over — otherwise the client's first transactional emails (sign-up confirmations) fail silently right when new members are signing up.
5. If the forum is enabled, confirm SSO is working (§6) before announcing it to members.
6. If the app was provisioned under a placeholder domain during server setup, update `SITE_DOMAIN` to the real one now.

## 9. Post-launch checks

- Site loads over HTTPS at the production domain.
- A test sign-up sends and receives a confirmation email.
- Staff notification emails arrive, if enabled (Q4).
- Forum SSO login works, if enabled (Q5).
- A test Xero invoice syncs, if enabled (Q5).
- The `fetch-invoice-updates` scheduled job has run at least once without error, if Xero is enabled.
- DigitalOcean's managed database backups are enabled (automatic on App Platform's managed Postgres, but confirm the retention window).
