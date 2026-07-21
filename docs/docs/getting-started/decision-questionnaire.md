# Decision questionnaire

**Who this page is for:** client decision-makers — the committee members approving costs and making decisions before your site is provisioned.

Work through every question below with your committee, then send your answers back to your provider in a single reply.
Read the [costs sheet](costs-sheet.md) alongside this page, since several questions affect what you'll pay.
Some questions decide a setting on your website; where that's the case, the question links to its entry in the [settings glossary](settings-glossary.md), which explains exactly what that setting changes.

## 1. Organisation name and domain

!!! warning "Get this one right before anything else starts"
    Changing your organisation's name or [domain](glossary.md#domain) after setup has begun causes real rework and cost — your provider has to re-provision your site under the new domain, and any connected services (like your [forum](glossary.md#forum)) may need renaming too.
    We've seen a rebrand mid-setup turn a smooth launch into weeks of extra work and an unplanned second domain purchase.
    Pick the exact name and domain you want to represent you today, before you go any further.

1. What is your organisation's exact legal or trading name?
2. What domain do you want (e.g. `example.org`)?
   Have you bought it yet?
3. If you don't have a domain yet: we recommend buying it through **Cloudflare** — it's usually cheaper than other registrars and adds basic bot/spam protection.
4. Who will own the domain account — this should be your organisation itself (for example, a shared account your committee controls), not a single volunteer's personal account, so control doesn't depend on one person staying involved.
5. Do you already have an old domain, website, or email address tied to contacts, subscriptions, or mailing lists that people still use?
   If so, tell us — we'll plan for keeping it reachable during the switch, rather than losing that traffic.

## 2. Languages

Which languages should your website be available in, and which one should be the primary/default language?
See [`AMS_ENABLED_LANGUAGES`](settings-glossary.md#ams_enabled_languages) for what this controls and which languages AMS currently supports.
The order you list them in is the order they'll appear in your site's language switcher.

## 3. Membership model

1. What membership types do you want (e.g. individual, organisation), and what does each cost?
   *Example: one association launched with a single flat introductory membership price for its first year, then introduced a full tiered pricing structure the year after — you don't need your final pricing model figured out before launch.*
2. For any free (zero-cost) membership type: should new sign-ups be approved automatically, or should a staff member review and approve each one first?
   See [`AMS_REQUIRE_FREE_MEMBERSHIP_APPROVAL`](settings-glossary.md#ams_require_free_membership_approval) for exactly what this changes.

## 4. Staff notification preferences

Should your staff/admin team get an email notification for each of the following?

1. Someone buys a membership, or an organisation adds more membership seats — see [`AMS_NOTIFY_STAFF_MEMBERSHIP_EVENTS`](settings-glossary.md#ams_notify_staff_membership_events).
2. A new organisation registers on your site — see [`AMS_NOTIFY_STAFF_ORGANISATION_EVENTS`](settings-glossary.md#ams_notify_staff_organisation_events).

Both default to on; most clients leave them on so nothing slips through unnoticed.

## Note: your everyday email vs your website's email

This isn't something you need to decide — just a distinction worth understanding before you read the costs sheet.

Your everyday staff/volunteer email — Google Workspace or whatever you already use — is completely separate from your website, and nothing about your AMS setup changes it.
Your website's own automatic emails (sign-up confirmations, password resets) use a separate [transactional email](glossary.md#transactional-email) service instead.
Migrating or changing your everyday email is a separate service, out of scope for your AMS setup.

## 5. Optional features

Which of these do you want switched on for launch?
Each can also be switched on later if you're not sure yet.

1. **Forum** — a discussion area for members, powered by Discourse (see the [forum admin guide](../admin/forum.md)).
   Has its own separate subscription cost — see the [costs sheet](costs-sheet.md).
2. **Events** — publish and manage events on your site.
   See [`AMS_EVENTS_ENABLED`](settings-glossary.md#ams_events_enabled).
3. **Resources** — a library of downloadable documents, files, and links for members.
   See [`AMS_RESOURCES_ENABLED`](settings-glossary.md#ams_resources_enabled).
4. **Xero billing** — automatically create invoices in Xero when someone buys a membership.
   Requires your own Xero account — see the [costs sheet](costs-sheet.md) and [accounts & access checklist](accounts-checklist.md).

Forum and Xero billing are configured directly by your provider based on your answer here, rather than through a setting listed in the settings glossary.

## 6. Data sovereignty / hosting region

Where your website's data is physically stored *(check with your provider as hosting arrangements vary and can change)*:

- **Default:** exactly where varies by provider, but generally your servers and static files (e.g. images) are stored in Australia.
  Your email service, forum (if you enable it), and server logs are stored in the EU or USA.
- **Country-specific option** (e.g. New Zealand): all of the above are stored in your chosen country instead.
  This raises both your setup cost and your ongoing hosting costs — by how much depends on your provider and chosen country, so ask before committing.

Tell us which option you want.
If data location isn't a concern for your organisation, the default is the faster and cheaper choice.

## 7. Branding assets

1. **Logo:** do you have a logo file ready?
   Your website can use PNG, JPEG, GIF, WEBP, AVIF, or SVG formats — a version with a transparent background works best if you have one.
2. **Colours:** do you have your brand colours as hex or RGB values (e.g. `#1A73E8`)?
   If you only have them "by eye" from existing material, that's fine too — your provider can match them.
3. **Fonts:** do you use particular fonts in your existing branding?
   A font name, or a file/URL where we can get it, is enough.
4. Who on your team supplies these — is it your committee, a volunteer, or an external designer/agency?
   If you're working with an external agency, send them the [working-with-designers](working-with-designers.md) page before they start.

## 8. Named roles

Tell us who holds each of the following — the same person can hold more than one role:

1. **Site admin** — has full control of your website's content and settings.
2. **Content loader(s)** — the volunteer(s) who will add your pages, events, and resources (see the [Building your website](../tutorials/index.md) tutorials).
3. **DNS controller** — whoever has access to your domain registrar account, since they'll need to add DNS records when asked.
4. **Credit-card holder** — for each service in the [accounts & access checklist](accounts-checklist.md), who is loading payment details?
   This can differ per service.

## 9. Reference site (optional)

Is there an existing website — yours or another organisation's — whose look or functionality you'd like your own site to start from?
This is optional, but it gives your provider a concrete starting point instead of building every choice from a blank page.

## What happens next

Send your answers back in a single reply, along with your completed [costs sheet](costs-sheet.md) review.
Your provider uses these answers to configure your site during the provisioning phase — see the [onboarding overview](index.md) for what happens after that.
