# Hosting AMS

**Who this page is for:** the provider — the person or team standing up and maintaining an AMS instance for a client.
Technical audience; terse runbook register.

AMS can be hosted on any platform that runs Docker containers.
This section starts with what any host needs, then gives the provider's own concrete worked example.

## What AMS requires of any host

- A **PostgreSQL database**.
- **S3-compatible media storage** (a public and a private bucket).
- An **email service provider (ESP)** for transactional email — Mailgun, Postmark, or Mailtrap.
- An **error-tracking sink and a log-ingestion sink** — both required today, regardless of platform.

[Deployment](deployment.md) covers the full requirements, environment variables, and container setup behind each of these, independent of platform.

## Pages in this section

- [Deployment](deployment.md) — what any AMS deployment needs, independent of platform: container requirements, the full environment variable reference, `deploy_steps`.
- [Worked example: DigitalOcean + Postmark + Cloudflare](provisioning-runbook.md) — ordered steps to stand up a new client instance on the provider's actual stack, from server setup through production cutover.
- [Backup & restore](backup-restore.md) — what needs backing up, how to restore it, and how to verify a restore worked.
- [Xero billing setup](xero-billing.md) — connecting Xero as an association's billing provider.
- [Client-communication templates](client-communication-templates.md) — copy-pasteable emails for the intake, UAT-handover, and launch handoffs.
