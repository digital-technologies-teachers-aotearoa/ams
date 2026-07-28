# Backup & restore

**Who this page is for:** the provider — the person restoring a broken AMS instance.
Technical audience; terse runbook register.

**Untested end to end.**
Nothing on this page has been exercised as a live disaster-recovery drill against a real client instance.
It's compiled from the platform's own documentation (dated where it matters) and general PostgreSQL/S3-compatible-storage practice, not verified against AMS in production.
Steps below are marked **(untested)** individually where that matters most; treat the whole page as a starting point, and do a rehearsal restore into a disposable environment before relying on it during a real incident.

The [costs sheet](../getting-started/costs-sheet.md) bills clients for "Backups, scheduled jobs & Xero sync," but until this page, nothing documented what that covers or how to actually use it.

## What needs backing up

AMS's own state is split across three things that all have to come back together, or a restore silently loses data:

1. **The PostgreSQL database** — every AMS-managed record: users, memberships, CMS pages, events, resources, settings.
2. **Media storage** — every uploaded image and file, split across a public S3-compatible bucket and a private one (see [Deployment: Requirements](deployment.md#requirements)).
    Pages and other database rows reference media by key, not by embedding the file itself, so the database and the buckets only make sense together.
3. **Environment variables and secrets** — `DJANGO_SECRET_KEY`, database credentials, storage keys, `XERO_*`, the ESP credential, observability tokens (see [Deployment: Environment variables](deployment.md#environment-variables)).
    These aren't part of a database or media backup at all — they live wherever your platform stores deployment config (for the provider's own stack, a GitHub Environment per deployment target, per the [worked example](provisioning-runbook.md#2-server-setup-digitalocean-app-platform)).
    Losing them means an intact database-and-media backup still can't be brought back online until they're re-entered from wherever else they're kept (a password manager, the GitHub Environment, etc.).

**Restoring the database without media, or media without the database, loses data.**
A database-only restore leaves every `Page` and `Resource` row pointing at images and files that no longer exist in the bucket.
A media-only restore brings back orphaned files nothing in the database references any more.
Always restore both together, from backups taken at the same time (or as close to it as your platform allows).

## What isn't covered here

- **Discourse (forum).**
  The production forum is Discourse's own hosted service (accounts checklist) — backups are Discourse's responsibility as part of that subscription, not the provider's.
  The UAT forum is different: it's self-hosted by the provider (see [Worked example §6](provisioning-runbook.md#6-discourse-instance-setup-sso-integration)), so Discourse's own backups don't apply to it, and this page doesn't establish a backup plan for it either — flagged as a gap, not solved here.
- **Xero.**
  Xero is the source of truth for invoices, not AMS — `fetch_invoice_updates` and webhooks keep AMS's copy in sync, but the invoices themselves live in the client's own Xero organisation and are Xero's to back up.

## Restore procedure (platform-agnostic)

Follow this order — media and secrets need to be in place before the app can serve requests, and you can't confirm the database restored correctly until it's actually running.

1. Provision a fresh database instance (or identify the restore target your platform's backup feature creates — see the worked example below).
2. Restore the database backup into it.
    For a platform without a managed restore feature, this is a standard PostgreSQL logical restore: create an empty database, then `pg_restore` (or `psql` for a plain-SQL dump) the backup file into it.
    Do this into a **fresh, unmigrated database** — the backup already contains a fully migrated schema, so don't run `manage.py migrate` first.
3. Restore the media backup into the public and private buckets, matching the point in time of the database backup as closely as possible.
    How you do this depends entirely on how the media was backed up in the first place (bucket-to-bucket copy, local sync, or a bucket-level snapshot if your platform offers one) — there's no platform-agnostic command for this the way `pg_restore` covers the database.
4. Re-apply the environment variables and secrets (see "What needs backing up" above) to the app, pointing `POSTGRES_*` at the restored database and `DJANGO_MEDIA_PUBLIC_*` / `DJANGO_MEDIA_PRIVATE_*` at the restored buckets.
5. Deploy the app against the restored database and buckets.
    This runs `deploy_steps` (`migrate` then `setup_cms`) per [Deployment: Deployment steps](deployment.md#deployment-steps) — `migrate` is safe to run here even though step 2 said not to run it against the fresh dump, because by now the app is deploying normally against an already-restored database, not creating one from scratch.
6. Verify the restore (below) before pointing production DNS at it or telling anyone it's back.

### If `setup_cms` fails with "Root page not found" (untested)

This happens if the restore *truncates* the database's rows instead of replaying a full dump into an unmigrated one — for example `manage.py flush`, or a data-only restore (`pg_restore --data-only`) into a database that's already migrated.
Wagtail's root `Locale`/`Page`/`Collection` are created by data migrations inside the `wagtail` package itself, not by application code — truncating deletes those rows, and because Django only replays a migration's data-loading code on a real `migrate` (not on `flush` or a data-only restore), nothing recreates them.
`setup_cms` then fails with "Root page not found."
Run `python manage.py ensure_wagtail_root` to recreate them, then re-run `setup_cms` — see [`ensure_wagtail_root`](../developer/management-commands-catalog.md#ensure_wagtail_root), and the same trap as it hits the screenshot suite's own seeding script in [Documentation conventions](../developer/docs-conventions.md#how-to-regenerate-screenshots).
This isn't the expected path for a normal full-dump restore (step 2 above restores the whole schema and data together, migrations included) — it's a fallback for a restore that truncated rather than replayed, or that ran `migrate` on a fresh database and never actually loaded the dump.

## Verifying a restore worked

Don't consider a restore complete until all of these pass:

1. `deploy_steps` (or `migrate` + `setup_cms` run manually) completes without error.
2. The site loads over HTTPS and you can sign in as an existing user — confirms the database restored.
3. Open a CMS page that has an uploaded image, and confirm the image renders — confirms the media buckets restored and match the database.
4. If the forum is enabled, confirm SSO login still works.
5. If Xero billing is enabled, confirm the `fetch-invoice-updates` scheduled job runs without error at least once (see [Worked example §9](provisioning-runbook.md#9-post-launch-checks)).

## Worked example: DigitalOcean + Spaces

**Database (production).**
DigitalOcean's managed PostgreSQL databases (used for production per the [worked example](provisioning-runbook.md#5-uat-site-standup)) take automatic daily backups, retained for 7 days *(checked against DigitalOcean's own documentation, 2026-07)* — confirm the current retention window in the control panel before relying on it, per the [worked example](provisioning-runbook.md#9-post-launch-checks)'s existing post-launch check, since DigitalOcean's plan-level options for this have changed before and may again.
Point-in-time recovery within that window is available, at least on some plan tiers — DigitalOcean's own docs weren't specific about which, so confirm this is available for the plan in use before assuming it.
To restore: in the control panel, open the database cluster → **Actions** → **Restore from backup** → choose the latest transaction or a specific point in time.
This always creates a **new** cluster rather than restoring in place, named after the original with the backup date appended — point the app's `POSTGRES_*` variables at the new cluster's connection details once it's ready.

**Database (UAT) — App Platform's Dev Database does not support backups at all (untested against this project, sourced from DigitalOcean's docs).**
UAT is provisioned as a **Dev Database**, not a Managed Database (see [Worked example §5](provisioning-runbook.md#5-uat-site-standup)), and DigitalOcean's own documentation states plainly that dev databases don't support backups or restoration.
If a client needs UAT to be recoverable the same way production is, the only fix is upgrading UAT to a full Managed Database — there is no backup feature to enable on a Dev Database.
This is a real gap in the current setup, not a deliberate trade-off documented anywhere before now.

**Media (Spaces buckets, both environments) — no built-in backup either (untested against this project, sourced from DigitalOcean's docs).**
DigitalOcean Spaces has no automatic backup feature at all, for either bucket, in either environment.
Two options, per DigitalOcean's own guidance:

- **Bucket versioning** — off by default; enable via the Spaces API (not the control panel) per bucket.
  This protects against an accidental overwrite or delete (recovers a previous version of an object), but DigitalOcean is explicit that versioning **is not a backup** — a Spaces-wide incident still loses everything.
- **Sync to a second location** — periodically copy the bucket's contents elsewhere, e.g. `s3cmd sync s3://<bucket-name>/ /<local-destination>/` to local storage, or a tool like Rclone to copy to a second bucket (a different region or account, for real redundancy).
  There's no restore command to match — restoring means syncing the same way, in reverse, into a freshly created bucket.

As things stand, media in both buckets, in both environments, has no backup at all unless one of the two options above is set up — this page documents the options; it doesn't confirm either has been implemented for any current client instance.

## Related pages

- [Deployment](deployment.md) — what a deployment consists of (database, media, environment variables) that this page assumes.
- [Worked example: DigitalOcean + Postmark + Cloudflare](provisioning-runbook.md#9-post-launch-checks) — where the database-backup confirmation step lives in the provisioning flow.
- [Costs sheet](../getting-started/costs-sheet.md#recurring-and-one-off-costs) — the client-facing cost line this page explains the operational side of.
