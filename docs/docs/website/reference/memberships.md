# Memberships & organisations

**Who this page is for:** client website admins — the volunteers who run the day-to-day site once it's launched.

This is the standing reference for how memberships and organisations behave.
For a guided, step-by-step walkthrough of creating a membership type and approving your first application, see [Tutorial 6: Memberships](../setup/memberships.md) instead.

## Membership statuses

Every individual or organisation membership record has one of these statuses, shown wherever memberships are listed:

| Status | Meaning |
| --- | --- |
| **Pending** | Applied for, but not yet approved — or approved with a start date that hasn't arrived yet. |
| **Active** | Approved, and today is on or after the start date and before the expiry date. |
| **Expired** | The expiry date has passed. |
| **Cancelled** | Cancelled by a staff member before it expired. |

There's a fifth label, **None**, but it isn't a status a membership record can hold — it's what the admin shows for a person or organisation with no membership record at all.

Status is worked out fresh every time it's displayed, from the record's dates — nothing needs to run on a schedule to move a membership from Active to Expired, or from Pending to Active once its start date arrives.

### How a membership moves between statuses

1. **Applying creates a Pending record** — unless it's a free membership and [`AMS_REQUIRE_FREE_MEMBERSHIP_APPROVAL`](../../getting-started/settings-glossary.md#ams_require_free_membership_approval) is off, in which case it's approved immediately.
2. **A paid membership becomes Active automatically the moment its invoice is marked paid** in your invoicing system — there's nothing for you to do.
3. **A pending membership can also be approved by hand**, for a payment made outside the invoicing system (bank transfer, cash) or a free membership that needs sign-off: open the record in the Django admin, set **Approved datetime**, and save.
   See [Tutorial 6: Approving a membership](../setup/memberships.md#approving-a-membership) for the click-by-click version.
4. **Active flips to Expired on its own** once the expiry date passes — no email, no warning, nothing else changes automatically. There are no renewal-reminder emails to a member as their expiry date approaches; if you want members reminded, you'll need to check in with them yourself.
5. **Cancelling is a staff-only, by-hand action.** A member who asks to cancel doesn't have a self-service option — the "Cancel Membership" button on their account page tells them to contact you — so you cancel their record yourself in the Django admin by setting **Cancelled datetime**. Cancelled and Expired are both dead ends: neither status changes again.

## Staff notification emails

Two independent settings control who gets emailed, and about what — they don't overlap the way their names might suggest:

| Setting | Controls |
| --- | --- |
| [`AMS_NOTIFY_STAFF_MEMBERSHIP_EVENTS`](../../getting-started/settings-glossary.md#ams_notify_staff_membership_events) | A new individual membership application, a new organisation membership application, and an organisation buying extra seats mid-term. |
| [`AMS_NOTIFY_STAFF_ORGANISATION_EVENTS`](../../getting-started/settings-glossary.md#ams_notify_staff_organisation_events) | A brand-new organisation being registered on the site (before it has any membership at all). |

In other words, "an organisation buys a membership" and "an organisation adds seats" are membership events, not organisation events, for the purposes of these two flags — only "a new organisation is created" is gated by the organisation-events setting.

With `AMS_NOTIFY_STAFF_MEMBERSHIP_EVENTS` off, one exception still emails staff: a free membership that needs approval always sends the notification, since somebody still has to act on it.
You can tell an application needing approval apart from one that doesn't by its subject line: "REQUIRES APPROVAL: ..." versus "New Individual Membership: ..." / "New Organisation Membership: ...".

## Organisation memberships and seats

An organisation membership works like an individual one, but covers a number of seats instead of one person.

- **Seats** is the total number purchased for the membership; **Max seats** (set on the membership option) is an optional cap on how many seats an organisation can ever hold.
- **Occupied seats** counts organisation members who have accepted their invite and have an active user account — but only while the organisation's membership itself is Active or Pending. Once the membership expires or is cancelled, occupied seats reads as zero, even if the people are still listed as members.
- **Max charged seats** (also set on the option) caps how many of those seats are billed; any seats beyond that number are free. An organisation can add more seats mid-term — the added seats are billed pro-rata for the time remaining until the membership's expiry date, respecting the max-charged-seats cap if one is set.

## Invitations

An organisation admin invites someone by email from the organisation's page.
If the person already has an AMS account, the invite links to it automatically; if not, accepting the invite is part of their sign-up.
An invite can be revoked (before it's accepted) or resent at any time from the same page.
If all the membership's seats are already occupied when an invite is sent, the invite still goes out, with a warning to the admin that the invitee won't be able to accept it until a seat frees up — the same check applies again when they try to accept.

## Removing a member and admin roles

Each organisation member is either an **Admin** (can invite, remove, and promote members, and edit the organisation) or a plain **Member**.
An admin can remove any other member, but not themselves — a member always leaves via their own "Leave organisation" action instead.
Every organisation must keep at least one admin: you can't remove, demote, or leave as the last remaining admin — promote someone else first.

## Deactivating an organisation

A website admin or organisation admin can deactivate an organisation themselves only once it's down to a single remaining member (themselves) — the option is there to let someone close an organisation.
For every other case, deactivate it from the Django admin's **Organisations** list instead, using the **Deactivate selected organisations** action — that works regardless of how many members it has.
Either way, deactivating an organisation automatically cancels any of its non-cancelled memberships and revokes any invites that are still pending.

## A known quirk: the "active" banner for admins

`user_has_active_membership()` — the function that decides whether someone sees a "you have a current active membership" banner and gets member-only access — returns `True` immediately for any superuser, before it looks at their actual membership records.
That means a superuser account (which is what `create_sample_admin` creates, and what you'll be signed in as while managing the site) always shows as having an active membership, whatever its own membership rows actually say.
If you want to see what a real member sees, test with a non-superuser account instead.
