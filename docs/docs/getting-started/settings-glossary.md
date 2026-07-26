# Settings glossary

**Who this page is for:** client decision-makers filling in the [decision questionnaire](decision-questionnaire.md), and anyone who wants to know what a setting actually changes on the website.

Every setting below is something you decide during onboarding — it is not a technical detail you need to configure yourself.
The provider sets these for you, based on your answers to the [decision questionnaire](decision-questionnaire.md).
This page exists so you can see, in plain language, what each one actually does before you answer.

This list is checked automatically against the AMS codebase, so a setting can't be added or removed without this page being updated to match — see [Documentation conventions](../developer/docs-conventions.md#settings-glossary-anti-drift-check).

## `AMS_ENABLED_LANGUAGES`

| | |
|---|---|
| **Default** | `en` (English only) |
| **Decided by** | [decision questionnaire, question 2](decision-questionnaire.md#2-languages) |

Controls which languages your website is available in, and the order they appear in the language switcher.
AMS currently supports English and Te Reo Māori.
English should always be one of the languages you choose.

## `AMS_EVENTS_ENABLED`

| | |
|---|---|
| **Default** | `False` (off) |
| **Decided by** | [decision questionnaire, question 5](decision-questionnaire.md#5-optional-features) |

Turns the Events feature on or off.
When off, there is no events section anywhere on the public site or in the admin area — the pages simply don't exist.
When on, you can publish and manage events, with pages for upcoming events, past events, and individual event details.

## `AMS_RESOURCES_ENABLED`

| | |
|---|---|
| **Default** | `False` (off) |
| **Decided by** | [decision questionnaire, question 5](decision-questionnaire.md#5-optional-features) |

Turns the Resources feature on or off — a library of downloadable resources (documents, files, and links) that members can browse and search.
When off, there is no resources section anywhere on the public site or in the admin area.

## `AMS_NOTIFY_STAFF_MEMBERSHIP_EVENTS`

| | |
|---|---|
| **Default** | `True` (on) |
| **Decided by** | [decision questionnaire, question 4](decision-questionnaire.md#4-staff-notification-preferences) |

Sends your staff/admin team an email whenever someone buys a membership, or an organisation adds more membership seats.
Turning this off does not stop every notification — a free membership that needs approval still emails staff, since someone has to approve it either way.

## `AMS_NOTIFY_STAFF_ORGANISATION_EVENTS`

| | |
|---|---|
| **Default** | `True` (on) |
| **Decided by** | [decision questionnaire, question 4](decision-questionnaire.md#4-staff-notification-preferences) |

Sends your staff/admin team an email whenever a new organisation registers on the site.

## `AMS_REQUIRE_FREE_MEMBERSHIP_APPROVAL`

| | |
|---|---|
| **Default** | `False` (off — automatically approved) |
| **Decided by** | [decision questionnaire, question 3](decision-questionnaire.md#3-membership-model) |

Decides what happens when someone signs up for a free (zero-cost) membership.
Off: they are approved automatically and become a member straight away.
On: their membership sits pending until a staff member approves it.
