# Costs sheet

**Who this page is for:** client decision-makers — the committee members approving costs before your site is provisioned.

This page lists every cost your organisation will pay to run an AMS website, in one place.
Each service is billed to you directly by that third party, in the currency shown — your provider does not mark these up.
Prices change over time, so each line is stamped with the month it was last checked; ask your provider to confirm current prices before you commit.

## Recurring and one-off costs

Add up every row below (using the lower end of any range) and you get your total monthly bill — nothing above is folded into another row.

| Service | What it's for | Cost | How often | Notes |
|---|---|---|---|---|
| Domain registration | Your website's address, e.g. `example.org` | ~$25 USD | per year | See the [decision questionnaire](decision-questionnaire.md#1-organisation-name-and-domain) for buying advice. Price checked 2026-06. |
| Website hosting (DigitalOcean) | Runs your live website: the server, database, and file storage | ~$44 USD | per month | Server ~$24, database ~$15, file storage ~$5. Price checked 2026-02. |
| Testing (UAT) site | A second, smaller copy of your site for reviewing changes before they go live — see [UAT](glossary.md#uat) | ~$28 USD | per month | Covers UAT hosting (~$12) and UAT forum (~$16, if enabled). Stays available after launch too, for checking future changes. Price checked 2026-02. |
| Transactional email (Postmark) | Sends automatic emails your site generates on its own — sign-up confirmations, password resets, membership notices | $15 USD | per month | The Basic plan — this is the plan that supports adding your provider as a [team member](glossary.md#team-member), rather than sharing a single login. AMS requires this service to send any email at all; it isn't optional. Price checked 2026-07. |
| Forum hosting (Discourse) | Runs your members' [forum](glossary.md#forum), if you enable it | $100 USD, or $50 USD with proof of non-profit status | per month | Qualifying proof: an incorporation certificate, or documentation showing official tax-exempt status. Send it to `team@discourse.org`. Only applies if you enable the forum — see the [decision questionnaire](decision-questionnaire.md#5-optional-features). This is your **live** forum cost; the UAT site's forum cost is in the row above. Price checked 2026-06. |
| Backups, scheduled jobs & Xero sync | Automatic backups and behind-the-scenes maintenance tasks, including syncing with Xero if you enable it | $0.50–$3 USD | per month | Price checked 2026-02. Your provider follows a [written backup & restore procedure](../hosting/backup-restore.md) — a technical page, written for them, not you. |
| Xero Custom Connection | The Xero add-on required to connect AMS to your Xero account, if you enable Xero billing | $10 USD | per month | Charged directly by Xero through your own Xero account — your provider doesn't bill you for this, and it's separate from whatever Xero plan you already pay for. Only applies if you enable Xero billing — see the [decision questionnaire](decision-questionnaire.md#5-optional-features) and the [accounts & access checklist](accounts-checklist.md#billing-integration-example-xero) for how it's set up. Price checked 2026-07. |
| Provider fees | Your provider's own time — setup, support, and maintenance | Discussed separately | — | Not included in any figure on this page. |

### What this adds up to

Once launched, with the forum's non-profit discount applied and your UAT site kept running: adding every row above (except the annual domain, the Xero Custom Connection, and provider fees) comes to roughly **$137–$140 USD/month**, plus **~$25 USD/year** for your domain.
If you enable Xero billing, add **$10 USD/month** for the Xero Custom Connection to that total.
This does not include provider fees, which are discussed separately.

## Not billed through AMS

These are costs your organisation already has, or would have regardless of AMS — they aren't part of your website bill.

- **Google Workspace** — your organisation's everyday email and office software.
  Separate from, and unaffected by, [transactional email](glossary.md#transactional-email) above — see the glossary entry for why a website needs its own dedicated email service.
- **Xero** — your organisation's accounting software, if you use one for membership billing.
  You'd need your own Xero plan regardless of AMS.
  Connecting AMS to Xero does add one small extra cost of its own — the Xero Custom Connection row in the table above — which is billed by Xero, not your provider.
