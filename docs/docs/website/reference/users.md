# Users & permissions

**Who this page is for:** client website admins — the volunteers who run the day-to-day site, especially whoever is responsible for giving other people access.

Every account on your site can have several kinds of access, granted separately: whether they belong to a **Group**, whether they have **Staff status**, and whether they have **Superuser status**. This page explains what each one is for.

## The three controls, in brief

- **Group** — controls access to the CMS: which pages someone can add, edit, or publish.
- **Staff status** — controls access to the Django admin (what [Tutorial 1: Orientation](../setup/orientation.md) calls "Website Admin" access), where memberships, events, resources, and user accounts themselves are all managed.
- **Superuser status** — the broadest of the three, and needs Staff status ticked alongside it to actually be usable.

For exactly what each combination lets someone do, and how to grant them, see [Inviting your team: What each permission level does](../setup/inviting-your-team.md#what-each-permission-level-does).

## Changing an existing user's access

See [Inviting your team: Changing permissions for someone who already has an account](../setup/inviting-your-team.md#changing-permissions-for-someone-who-already-has-an-account) — the same steps apply whether you're changing a Group, Staff status, or Superuser status.

## Editing a user from the CMS

As well as the Django admin, CMS admins can edit a user's name, email, and username at `/cms/users/<id>/` — Wagtail's own simpler Users area — without switching over to the Django admin.
