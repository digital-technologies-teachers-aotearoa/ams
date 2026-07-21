---
render_macros: true
---

# Client-communication templates

**Who this page is for:** the provider, running a client onboarding.

Three copy-pasteable email templates for the handoffs that recur on every onboarding: first contact, UAT handover, and launch.
Reusing proven wording avoids re-drafting each one from scratch, and keeps the wording consistent across clients.

## How to use these templates

- Replace every `{{placeholder}}` before sending — none of them should reach a client's inbox.
- Each template links directly to the public docs site (`https://digital-technologies-teachers-aotearoa.github.io/ams/...`), so links can be copied straight into an email with no editing.
  The page source writes these as `{{ config.site_url }}<path>` rather than the site's usual relative Markdown links; the `mkdocs-macros` plugin (opted into on this page only, via its YAML front matter — see `developer/docs-conventions.md`) substitutes the real base URL at build time.
  The strict docs build doesn't check these particular link targets the way it checks ordinary Markdown links, so re-verify them by hand if a linked page is ever renamed or moved.
- Between sends, especially during the accounts and UAT phases, a running **TODO / IN PROGRESS / DONE** list — each item owned by a named person, with a due date — keeps both sides aligned without a new email per item.
- If a phase stalls, ask the client for their **top 3** outstanding items rather than the whole remaining list; once they clear one, ask for the next.
  This cadence works better than requesting everything at once.

## 1. Intake email

Send this at first contact, once you're ready to start a new client's onboarding.

**Subject:** Getting your {{organisation}} website started

> Hi {{contact_name}},
>
> Thanks for choosing AMS for {{organisation}}'s new website.
> Before we can start building your site, we need your decisions and your accounts set up on your side.
> We've tried to make this a single round trip: please read the four pages below, work through them, then reply to this email once with your questionnaire answers and confirmation that every account is created (with us invited on each one).
>
> 1. [Getting started]({{ config.site_url }}getting-started/) — how the whole process works, from your first decisions through to launch day.
> 2. [Decision questionnaire]({{ config.site_url }}getting-started/decision-questionnaire/) — the decisions we need from you: your organisation's name and domain, languages, membership model, and more.
> 3. [Costs sheet]({{ config.site_url }}getting-started/costs-sheet/) — every cost you'll see, all in one place.
> 4. [Accounts & access checklist]({{ config.site_url }}getting-started/accounts-checklist/) — the accounts you'll need to create, and exactly which plan to buy on each one.
>
> If you're working with an external designer or agency on your branding, please also pass them our [working with designers]({{ config.site_url }}getting-started/working-with-designers/) page — it explains what AMS can and can't do for their design work.
>
> Once we have your questionnaire answers and confirmation that every account is set up, we'll get started building your site.
>
> Thanks,
> {{your_name}}

## 2. UAT-handover email

Send this once the [UAT site]({{ config.site_url }}getting-started/glossary/#uat) is ready for the client to check.

**Subject:** Your {{organisation}} site is ready for checking

> Hi {{contact_name}},
>
> Your website is ready for checking at {{uat_url}}.
> This is your UAT site: a private, working copy of your website where you and your team can try everything before it goes live.
>
> Please sign up and check:
>
> - Every page reads correctly, in every language you've enabled.
> - Sign-up and sign-in work as you'd expect.
> - Anything else that looks wrong or missing.
>
> If you find anything, please add it to this shared list rather than emailing separately: {{feedback_sheet_url}}.
> We'll work through it as items come in.
>
> Thanks,
> {{your_name}}

## 3. Launch checklist email

Send this once production cutover is complete and the site is live.

**Subject:** {{organisation}} is live!

> Hi {{contact_name}},
>
> Your website is now live at {{production_url}}.
>
> One thing worth telling your members: there are always a few refinements and bits of tidying still to do just after launch, so please don't be alarmed if something looks slightly unfinished.
> We focused on making sure everyone could see and use all the site's functionality first, and we'll keep polishing in the background.
>
> Feel free to share that reassurance with your members alongside your launch announcement.
>
> Thanks,
> {{your_name}}
