# Glossary of terms

**Who this page is for:** client decision-makers and client website admins — look up any unfamiliar term used elsewhere in these docs.

You don't need to memorise any of this.
Other pages link straight to the entry you need, the first time a term appears.
Terms are listed alphabetically.

## CMS

A CMS (content management system) is the software you use to add, edit, and publish pages on your website — text, images, and layout — without writing any code.
AMS's CMS is called Wagtail; you'll use it every time you update a page (see the [Building your website](../tutorials/index.md) tutorials).

## DNS

DNS (Domain Name System) is the internet's address book.
It translates your domain name, like `example.org`, into the technical address computers use to actually find your website.
You don't need to understand how it works, but you may occasionally need to add a [DNS record](#dns-record) when your provider asks you to.

## DNS record

A DNS record is a single instruction stored against your domain, usually added through your [registrar](#registrar)'s website.
Different records do different jobs — one might point your domain at your website's hosting, another at your email service.
Your provider will tell you exactly which record to add and what value to put in it; you won't need to choose these yourself.

## Domain

Your domain is your website's address, such as `example.org`.
You buy a domain from a [registrar](#registrar), and it stays yours as long as you keep renewing it.
Changing your domain later is possible, but it causes real rework and cost, so it's worth locking in your exact name and domain before anything else is set up.

## Env var

An env var (environment variable) is a piece of configuration that controls how your website's software behaves — for example, which language it defaults to, or whether a feature like events is switched on.
Some env vars are also called settings; every AMS setting you get to decide is listed in the [settings glossary](settings-glossary.md), in plain language.
You won't set these yourself — your provider configures them based on your answers during onboarding.

## Forum

The forum is the discussion area of your website, where members post and reply to each other.
AMS's forum is powered by a separate product called Discourse, connected to your main site so members sign in once (see [SSO](#sso)) instead of needing a second password.
See the [forum admin guide](../admin/forum.md) for how it's set up and run.

## Hosting

Hosting is the service that keeps your website switched on and reachable on the internet, day and night.
Think of it like renting space for your site to live in: a hosting company supplies the server, and your provider manages what runs on it.

## Production

Production is the live version of your website — what the public and your members actually see and use.
Changes are checked on a private copy first (see [staging](#staging) and [UAT](#uat)) before they go live on production.

## Provider

Your provider is the company or person who builds, sets up, and maintains your AMS website for you.
You make the decisions — organisation details, features, branding; the provider does the technical work: creating accounts, configuring settings, and keeping the site running.

## Registrar

A registrar is the company you buy your domain from.
It's usually also where you manage your domain's [DNS records](#dns-record) and renew the domain each year so you don't lose it.

## SSO

SSO stands for single sign-on.
It means signing in once on your main website and being automatically recognised on a connected service too — for AMS, that's the [forum](#forum) — instead of needing a separate password for each one.

## Staging

A staging site is a private, work-in-progress copy of your website, used to test and review changes before they go live.
AMS's staging site is usually called the UAT site — see [UAT](#uat).

## Subdomain

A subdomain is an addition placed in front of your main [domain](#domain), such as `members.example.org`.
It's used to run something separate under your main domain — for example, giving an external design agency's site its own address while your AMS site lives on a subdomain of the same domain.

## Team member

A team member (sometimes called a collaborator) is a person you invite into one of your organisation's online accounts, so they can help manage it without you sharing the account owner's password.
Some subscription plans only allow one person on the account at all, so it's worth checking the plan details before you buy — upgrading later can cost extra money and cause delays.

## Transactional email

Transactional email is an automatic email your website sends on its own, like a signup confirmation or a password reset link.
It's different from your everyday email inbox (like Google Workspace) — a website needs a dedicated transactional email service so these automatic emails reliably arrive, rather than getting flagged as spam.

## UAT

UAT stands for User Acceptance Testing.
It's a private version of your website where you and your team check that everything works and looks right before the public launch.
You'll be given a link to your UAT site partway through onboarding and asked to review it before it becomes your live [production](#production) site.
