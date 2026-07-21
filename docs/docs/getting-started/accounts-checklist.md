# Accounts & access checklist

**Who this page is for:** client decision-makers and the volunteer who will set up your third-party accounts.

Work through each service below: create the account, buy the right plan, and grant your provider access the correct way.
Every service listed here has a way to give your provider access **without** handing over your password or credit card — use it, even if it feels slower than just sharing a login.
This page names the specific services one AMS provider actually uses, as a worked example — your provider may use different ones for the same job, so check with them if anything here doesn't match what they've told you.

!!! danger "Never share credit cards or passwords"
    Don't email, message, or read out a card number or a login password to your provider for any of these services — not even "just this once" to save time.
    Every service below has a proper way to grant access instead: an invite, a team, or an authorisation link.
    If a step below doesn't cover the access your provider is asking for, ask them for the correct method rather than sharing credentials.

Billing integration and Forum are only needed if you chose those [optional features](decision-questionnaire.md#5-optional-features) in the decision questionnaire — skip those two sections if you didn't.
Costs for every service are in the [costs sheet](costs-sheet.md); this page covers the plan to pick and how to grant access, not the price.

## Transactional email (example: Postmark)

Do this one first.
Your provider can't get your testing ([UAT](glossary.md#uat)) site ready until they have access to your transactional email service, so setting it up before the other services on this page avoids it becoming the bottleneck.

**Account and plan:** the **Basic plan**, $15 USD/month (see the [costs sheet](costs-sheet.md)).
This is the plan that supports adding your provider as a [team member](glossary.md#team-member) — confirm you're on Basic (not a lower-tier plan) before inviting anyone, so you don't have to redo the signup on a different plan later.

**Where to load payment:** you'll be asked for payment details when you sign up for the Basic plan.

**How to grant access:**

1. Sign in to Postmark and click **Account** in the top navigation.
2. Select the **Users** tab.
3. Click **Invite user**.
4. Enter your provider's name and email address.
5. Under **Role**, choose **Technical** — this role is built for developers: it can manage servers and API access, but it can't see your billing details or invoices.
6. Click **Send invitation**.

Your provider will get an email with a link to set up their own login — you never share yours.

*(Plan name, price, and role names checked 2026-07.)*

**FAQ: "We already have Google Workspace email addresses — can we use those instead of Postmark?"**
No — they do different jobs.
[Transactional email](glossary.md#transactional-email) is what your *website* sends automatically (sign-up confirmations, password resets); it needs a dedicated service like Postmark to arrive reliably instead of getting flagged as spam.
Google Workspace is your team's own everyday inboxes, and stays completely separate — see the [decision questionnaire](decision-questionnaire.md#note-your-everyday-email-vs-your-websites-email).

## Domain registrar (example: Cloudflare)

*(Skip this if you already bought your domain — see [decision questionnaire, question 1](decision-questionnaire.md#1-organisation-name-and-domain).)*

**Account and plan:** a free Cloudflare account.
No paid Cloudflare plan is needed just to manage [DNS](glossary.md#dns) — you only pay for the domain itself (see the [costs sheet](costs-sheet.md)).

**Where to load payment:** in the Cloudflare dashboard, when you buy or transfer in your domain.

**How to grant access:**

1. Sign in to your Cloudflare dashboard.
2. Go to **Manage Account → Members**.
3. Click **Invite**.
4. Enter your provider's email address.
5. Under **Roles**, choose **Domain DNS**, scoped to your domain only — not full account access.
6. Click **Continue to summary** and check the details.
7. Click **Invite**.

The Domain DNS role only lets your provider edit [DNS records](glossary.md#dns-record) for your domain.
It can't see your billing details or any other part of your Cloudflare account.

*(Plan and role names checked 2026-07 — Cloudflare may change these; if a label below doesn't match what you see, use the closest equivalent and ask your provider to confirm.)*

## Hosting (example: DigitalOcean)

**Account and plan:** a DigitalOcean account with a **Team** created under it — not a personal account on its own.
A team is what lets you add your organisation's payment method and invite your provider without sharing a login.
There's no separate "plan" to choose here; your hosting costs are the [DigitalOcean hosting rows on the costs sheet](costs-sheet.md), sized by your provider to what your site needs.

**Where to load payment:** as part of creating the team, below.

**How to grant access:**

1. Create a DigitalOcean account (ask your provider if they have a referral link).
2. Click the profile icon in the top right.
3. Click **Create a Team**.
4. On the **Team Info** tab, enter your organisation's name and a contact email.
5. On the **Add Payment Method** tab, enter your organisation's card.
6. On the **Invite Team Members** tab, enter your provider's email address.
7. Click **Send Invites**.

If you skip that last step, you can invite your provider later: go to **Team Settings** and click **Invite Members**.

*(Steps checked 2026-07.)*

## Billing integration (example: Xero)

*(Only needed if you chose Xero billing in [decision questionnaire, question 5](decision-questionnaire.md#5-optional-features).)*

**Account and plan:** your organisation's own Xero subscription — any plan, chosen for your organisation's accounting needs, unrelated to AMS.
Connecting AMS to Xero also needs a **Custom Connection subscription**, a separate Xero add-on for integrations like this one, $10 USD/month, charged directly through your own Xero account rather than by your provider (see the [costs sheet](costs-sheet.md) and [Xero's Custom Connection page](https://connect.xero.com/custom)).

**How to grant access:**

Xero access works differently from the other services — you don't invite your provider into your Xero account at all, and no login is ever shared.

1. Tell your provider you're ready to connect Xero.
2. Give them the name and email address of whoever has admin access to your Xero organisation.
3. Your provider sets up the connection on Xero's side and lists that person as the **authorising user**.
4. That person gets an email directly from Xero with a link to authorise the connection.
5. They click the link and check the access being requested — Xero shows exactly what it covers (contacts and invoices, nothing else in your Xero account).
6. They choose your organisation and confirm.

**FAQ: "How do I give you Xero access?"**
That's exactly the steps above — an email from Xero itself, not a password you hand over.

## Forum (example: Discourse)

*(Only needed if you chose the forum in [decision questionnaire, question 5](decision-questionnaire.md#5-optional-features).)*

**Account and plan:** the Discourse **Pro** plan, $100 USD/month, or $50 USD/month once the non-profit discount is applied (see the [costs sheet](costs-sheet.md)).
Do this once your provider tells you your forum is ready — it's set up as part of provisioning, not something you create from scratch yourself.

**Where to load payment and how to grant access:**

1. Once your provider says your forum is ready, sign up for a personal account on your forum's website using your own name and email.
   This account is temporary.
2. Ask your provider to grant that account admin access, temporarily.
3. Go to `<your-forum-address>/admin/manage-account`.
4. Click **Start Subscription** and choose the **Pro** plan.
   You can start on the Free plan instead if you want to trial it first, but the non-profit discount only applies to Pro (or Business), so you'll need to move to Pro before requesting it.
5. Enter your organisation's payment details.
6. Once your subscription is running, send your proof of non-profit status (see the FAQ below) to apply the discount.
   Discourse applies the discount to an existing subscription — you need to sign up first, since there's nothing yet for the discount to apply to.
7. Tell your provider once you're done.
   They'll remove your temporary personal account — after that, members (including you) sign in to the forum automatically through your main website ([SSO](glossary.md#sso)) instead of a separate forum password.

**FAQ: "Who do we send proof of non-profit status to?"**
Send proof — an incorporation certificate, or documentation showing official tax-exempt status — to `team@discourse.org`, once your subscription is already running.

*(Plan, price, and this setup process checked 2026-07 — this is the same process used successfully during a previous AMS onboarding.)*

## What happens next

Once you've worked through the services that apply to you, tell your provider — they'll confirm every access grant went through and start [provisioning](index.md) your site.
