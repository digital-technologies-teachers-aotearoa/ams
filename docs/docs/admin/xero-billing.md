# Xero Billing Setup Guide

This guide walks you through setting up Xero as the billing provider for your AMS installation. This is a one-time setup process that must be completed before deploying the AMS website.

## Overview

AMS integrates with Xero to handle:

- Creating and managing customer contact records
- Generating invoices for memberships and services
- Sending invoice emails to customers
- Tracking invoice payment status automatically via webhooks
- Synchronizing invoice data between AMS and Xero

## Prerequisites

Before you begin, ensure you have:

- **Xero account** with administrator access to your organization
- **Xero Custom Connection subscription** - See [Xero's Custom Connection documentation](https://connect.xero.com/custom) for details
    - **Note:** The Xero Demo Company can be used for free during testing and development
- **Access to the Xero Developer Portal** at [https://developer.xero.com/](https://developer.xero.com/)
- **The domain name** where your AMS website will be hosted (for webhook configuration)

## Step 1: Create a Custom Connection in Xero

1. Navigate to [Xero My Apps](https://developer.xero.com/app/manage) in the Xero Developer Portal
2. Click **"New App"** button
3. Fill in the application details:
    - **App name:** Give it a descriptive name (e.g., "AMS Billing Integration" or "Association Management Billing")
    - **Integration type:** Select **"Custom connection"**
    - **Company or application URL:** This is not used as part of the integration, just a reference of the website. Enter your domain here.
4. Click **"Create app"**

## Step 2: Configure App Scopes

After creating the app, you'll need to select which permissions (scopes) the integration requires:

1. In your app's configuration page, locate the **"OAuth 2.0 Scopes"** section
2. Select the following scopes:
    - ✅ **`accounting.contacts`** - Required for creating and managing customer contacts
    - ✅ **`accounting.transactions`** - Required for creating, retrieving, and managing invoices
3. Click **"Save"** to apply the scope changes

## Step 3: Authorize the Connection

1. In the **"Select the authorizing user"** section, choose the Xero user who will authorize the connection
    - This user must have the appropriate permissions in your Xero organization
2. The selected user will receive an email with an authorization link
3. Have them:
    - Click the link in the email
    - Review and consent to the requested scopes
    - Select the Xero organization to connect to AMS
    - Complete the authorization

!!! note "Custom Connection Subscription"
    Your organization must have an active [Custom Connection subscription](https://connect.xero.com/custom) to use this integration in production. For testing and development, you can use the Xero Demo Company for free.

## Step 4: Retrieve API Credentials

Once the connection is authorized, you need to collect several pieces of information to provide to your deployment team.

### Client ID and Client Secret

1. In the Xero Developer Portal, go to your app's configuration page
2. Locate the **"Client credentials"** section
3. Copy the **Client ID** - this is your `XERO_CLIENT_ID`
4. Click **"Generate a secret"** if you haven't already
5. Copy the **Client Secret** immediately - this is your `XERO_CLIENT_SECRET`

    !!! warning "Important"
        The client secret is only shown once. Store it securely - you won't be able to see it again. If you lose it, you'll need to generate a new one.

## Step 5: Configure Webhooks

Webhooks allow Xero to notify AMS when invoice status changes (e.g., when an invoice is paid).

!!! tip "Webhook URL Requirements"
    - Make sure your AMS deployment is accessible before configuring the webhook
    - The webhook URL must be HTTPS (secure connection)
    - Xero will send a test request to verify the endpoint during setup

1. In the Xero Developer Portal, go to your app's configuration page
2. Navigate to the **"Webhooks"** section.
3. For the 'Notify this app about changes to' field, select 'Contacts' and 'Invoices'.
4. Enter your webhook URL:
    - Format: `https://YOUR_DOMAIN/billing/xero/webhooks/`
    - Example: `https://members.example.org/billing/xero/webhooks/`
5. A **Webhook Key** will be automatically generated - this is your `XERO_WEBHOOK_KEY`
6. Copy this webhook key and store it securely
7. Click **"Save"**

## Step 6: Collect Required Values

### Tenant ID (Organization ID)

1. Within your app on the Xero Developer Portal, select "Connection management"
2. The Tenant ID will be listed here - this is your `XERO_TENANT_ID`

### Account Code

The Account Code determines which account in your Xero Chart of Accounts will be used for invoice line items.

1. Log into your Xero organization
2. Navigate to **Accounting** → **Chart of Accounts**
3. Identify the account you want to use for membership fees and services
    - Common choices include revenue accounts like "Sales" (often code `200`) or "Membership Income"
4. Note the **Code** column value for that account - this is your `XERO_ACCOUNT_CODE`

### Currency and Tax Settings

Based on your organization's location and Xero setup, determine:

- **Currency Code:** The 3-letter ISO currency code (e.g., `NZD`, `AUD`, `USD`, `GBP`, `EUR`)
    - This is your `XERO_CURRENCY_CODE`
- **Amount Type:** How tax is calculated on invoices:
    - `INCLUSIVE` - Line item amounts include tax
    - `EXCLUSIVE` - Tax is added on top of line item amounts
    - This is your `XERO_AMOUNT_TYPE`

## Step 7: Prepare Credentials for Deployment

Once you've collected all the required information, you need to provide it to your deployment team or system administrator. Prepare a secure document containing:

### Required Credentials

| Variable Name | Description | Your Value |
|---------------|-------------|------------|
| `AMS_BILLING_SERVICE_CLASS ` | Required to use Xero billing | `ams.billing.providers.xero.XeroBillingService` |
| `XERO_CLIENT_ID` | OAuth2 Client ID from Step 4 | |
| `XERO_CLIENT_SECRET` | OAuth2 Client Secret from Step 4 | |
| `XERO_TENANT_ID` | Organization/Tenant ID from Step 4 | |
| `XERO_WEBHOOK_KEY` | Webhook signing key from Step 5 | |
| `XERO_ACCOUNT_CODE` | Chart of Accounts code from Step 4 | |
| `XERO_AMOUNT_TYPE` | Either `INCLUSIVE` or `EXCLUSIVE` | |
| `XERO_CURRENCY_CODE` | 3-letter currency code (e.g., `NZD`) | |

### Optional Configuration

| Variable Name | Description | Recommended Value |
|---------------|-------------|-------------------|
| `XERO_EMAIL_INVOICES` | Enable/disable invoice emails | `True` for production, `False` for Demo Company (unsupported by Xero) |
| `AMS_BILLING_EMAIL_WHITELIST_REGEX` | Filter invoice email recipients (for testing) | Leave empty for production |

!!! danger "Security Warning"
    These credentials provide access to your Xero organization's financial data. Handle them with extreme care:

    - Use a secure method to transmit credentials (encrypted email, password manager, secure portal)
    - Never commit credentials to version control
    - Never share credentials in plain text chat or unencrypted email
    - Restrict access to only those who need it
    - Consider using a password manager or secrets management system

## Testing with Xero Demo Company

For development and testing purposes, you can use the Xero Demo Company instead of a production organization:

1. When authorizing the Custom Connection in Step 3, select the **"Demo Company"** instead of your production organization
2. The Demo Company is free and comes with sample data
3. Set `XERO_EMAIL_INVOICES=False` in your environment variables when using the Demo Company to prevent sending test emails
4. You can create and manage test invoices without affecting real financial data

!!! warning "Demo Company Limitations"
    - Demo Company data may be reset periodically
    - Some features may behave differently than in production organizations
    - Always perform final testing in a production-like environment before going live

## Verifying the Integration

After your deployment team has configured AMS with the credentials:

1. Log into the AMS website as a user
2. Try creating a membership
4. Verify that:
    - Contact is created in Xero
    - Invoice appears in Xero with correct details
    - Once paid in Xero, the membership is marked as paid within the AMS website

## Troubleshooting

### "Invalid credentials" or "Unauthorized" errors

- Double-check that `XERO_CLIENT_ID` and `XERO_CLIENT_SECRET` are correct
- Ensure the Custom Connection is still authorized
- Verify the user who authorized the connection still has appropriate permissions

### Invoices not appearing in Xero

- Verify `XERO_TENANT_ID` matches your organization
- Check that the scopes `accounting.contacts` and `accounting.transactions` are enabled
- Review application logs for API errors

### Webhook not receiving updates

- Verify the webhook URL is correct and accessible via HTTPS
- Check that `XERO_WEBHOOK_KEY` matches the key in Xero Developer Portal
- Test the webhook endpoint manually or check Xero's webhook delivery logs

### Invoice emails not sending

- Verify `XERO_EMAIL_INVOICES=True` in your environment variables
- Check that contact email addresses are valid in Xero
- If using Demo Company, email sending is disabled by default

### Rate limiting errors

If you encounter rate limiting errors (too many API requests):

- Xero has API rate limits (60 requests per minute)
- The AMS system handles this automatically with exponential backoff
- If issues persist, contact your developer team to review API usage patterns
- Consider spreading bulk operations (like importing many members) over time

## Next Steps

Once the Xero integration is configured and verified:

- Train your team on how to use the billing features in AMS
- Set up your membership plans and pricing
- Configure invoice templates in Xero (if desired)
- Establish billing workflows and processes
- Monitor the integration during the first billing cycle

For additional support, contact your AMS implementation team or refer to the [developer documentation](../developer/billing.md).
