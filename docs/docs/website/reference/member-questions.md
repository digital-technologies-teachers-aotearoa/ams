# Questions members ask

**Who this page is for:** client website admins — quick answers to give a member who asks you something directly, not a page written for members to read themselves.

This documentation is written for the people running the site, not the people using it — nothing here is meant for a member to browse on their own.
This page exists so that when a member emails or messages you with a question, you have a short, accurate answer ready to forward, rather than guessing.

## "How do I update my profile or contact details?"

They sign in and go to their account page, then **Edit Profile**.
Any field you've added as a [custom profile field](../setup/profile-fields.md) shows up there too, alongside name, email, and the built-in fields.

## "How do I renew my membership?"

There's no separate "renew" button — they apply again the same way they joined the first time, from the **Register for a new individual membership** link on their account page, choosing a start date on or after their current membership's expiry date.
This creates a new application the same way a first-time application does; see [how a membership moves between statuses](memberships.md#how-a-membership-moves-between-statuses).

**There are no automated renewal reminder emails.** If you want members reminded before their membership expires, that's on you to do — nothing in AMS currently emails them automatically. A member checking their own account page can see their own expiry date, if they think to look.

## "How do I cancel my membership?"

They can't do this themselves — the **Cancel Membership** button on their account page tells them to contact you.
You cancel it for them from the Django admin; see [Cancelling is a staff-only, by-hand action](memberships.md#how-a-membership-moves-between-statuses).

## "What does 'Pending' / 'Active' / 'Expired' mean next to my membership?"

Point them at the [membership statuses table](memberships.md#membership-statuses).
In short: **Pending** means applied but not yet approved (or approved but not yet started), **Active** means current, **Expired** means the end date has passed, and **Cancelled** means a staff member cancelled it before it expired.

## "How do I get into the forum?"

If they have an active membership, they just click through to the forum from the site — they're signed in automatically, with no separate forum account or password to set up (see [SSO](../../getting-started/glossary.md#sso)).
An active membership is what unlocks it; someone with no active membership, or an expired one, is shown a sign-in prompt instead of the forum itself.

## "I forgot my password — what do I do?"

**Forgot your password?** on the sign-in page sends them a reset email themselves — you don't need to do anything, and you can't see or reset it for them.

## "How do I add someone to my organisation, or remove them?"

Only an organisation **Admin** can do this, from the organisation's own page — invite by email, remove a member, or promote someone else to Admin.
See [Invitations](memberships.md#invitations) and [Removing a member and admin roles](memberships.md#removing-a-member-and-admin-roles) for the details, including the rule that an organisation always needs at least one Admin.

## "Why can't I see this page?"

If a page is marked **Members only**, anyone without an active membership — including a member whose membership has expired — gets a "not found" response instead of the page.
See [Public or Members only](cms.md#page-types) in the CMS reference.

## "Can I use the site in another language?"

If your site has more than one language configured, a language switcher is available in the site footer for signed-in members (and in the header for visitors who aren't signed in yet).
See [Languages & translations](../setup/languages-translations.md) if they're asking because a page looks untranslated — that's a content gap for you to fill in, not something they can fix themselves.
