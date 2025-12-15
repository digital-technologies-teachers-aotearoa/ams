# Billing Integration

AMS uses a pluggable billing service architecture that allows integration with various billing providers. Currently, Xero is the supported billing provider using the Custom Connection flow.

## Overview

The billing system handles:

- Creating and managing customer contacts
- Generating invoices for memberships and services
- Sending invoice emails
- Tracking invoice payment status via webhooks
- Synchronizing invoice data between AMS and the billing provider

## Xero Integration

### Custom Connection Flow

AMS uses Xero's **Custom Connection** authentication flow, which is designed for single-organization integrations. This approach:

- Uses OAuth2 client credentials grant type
- Connects to a single pre-authorized Xero organization
- Requires no interactive user authentication
- Is ideal for backend integrations like AMS

**Important:** Before configuring AMS, you must set up a Custom Connection in the Xero Developer Portal following the steps below.

### Setting Up a Xero Custom Connection

1. **Create the Custom Connection** in [Xero My Apps](https://developer.xero.com/app/manage):
    - Click "New App"
    - Give it a name (e.g., "AMS Billing Integration")
    - Select **"Custom connection"** as the integration type

2. **Select Required Scopes:**
    - ✅ `accounting.contacts` - For creating and managing customer contacts
    - ✅ `accounting.transactions` - For creating, retrieving, and managing invoices

3. **Select the Authorizing User:**
    - Choose the user who will authorize the connection
    - They will receive an email with a link to authorize

4. **Authorize the Connection:**
    - The selected user clicks the link in their email
    - They consent to the requested scopes
    - They select the Xero organization to connect
    - **Note:** The organization must have purchased a [Custom Connection subscription](https://connect.xero.com/custom) (the Xero Demo Company can be used for free during development)

5. **Retrieve Credentials:**
    - Once authorized, return to the app details page
    - Copy the **Client ID**
    - Generate and copy the **Client Secret** (keep this secure!)
    - Note your **Tenant ID** (organization ID) from the connection details

### Configuration

Configure the following environment variables for Xero integration:

#### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AMS_BILLING_SERVICE_CLASS` | The billing service provider class | `ams.billing.providers.xero.XeroBillingService` |
| `XERO_CLIENT_ID` | OAuth2 client ID from your Custom Connection | `91E5715B1199038080D6D0296EBC1648` |
| `XERO_CLIENT_SECRET` | OAuth2 client secret from your Custom Connection | `your-secret-here` |
| `XERO_TENANT_ID` | Xero organization/tenant ID | `a3a4dbaf-3495-a808-ed7a-7b964388f53` |
| `XERO_WEBHOOK_KEY` | Webhook signing key for validating webhook requests | `your-webhook-key` |
| `XERO_ACCOUNT_CODE` | Default account code for invoice line items | `200` |
| `XERO_AMOUNT_TYPE` | Tax calculation type | `INCLUSIVE` or `EXCLUSIVE` |
| `XERO_CURRENCY_CODE` | Currency code for invoices | `NZD`, `AUD`, `USD`, etc. |

#### Optional Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AMS_BILLING_EMAIL_WHITELIST_REGEX` | Regex pattern to filter invoice email recipients (for testing) | `@example.com$` |

### Webhook Configuration

AMS receives webhook notifications from Xero when invoice status changes (e.g., paid, voided).

1. **Configure the webhook endpoint** in your Xero app settings:
    - Webhook URL: `https://your-domain.com/billing/xero/webhooks/`
    - Generate a webhook key and set it as `XERO_WEBHOOK_KEY`

2. **Webhook Events Handled:**
    - Invoice creation
    - Invoice updates
    - Invoice payments

The webhook endpoint automatically verifies requests using HMAC-SHA256 signature validation.

### Local Development

For local development with webhooks:

1. Use [ngrok](https://ngrok.com/) or similar tool to expose your local server:

    ```bash
    ngrok http 8000
    ```

2. Set the `NGROK_HOST` variable in your `.envs/.local/django-private.ini`:

    ```ini
    NGROK_HOST = "your-subdomain.ngrok-free.dev"
    ```

3. Update your Xero app webhook URL to point to your ngrok URL:

    ```text
    https://your-subdomain.ngrok-free.dev/billing/xero/webhooks/
    ```

### API Operations

The Xero billing service performs the following operations:

#### Contact Management

- **Create Contact:** Creates a new contact in Xero when a user or organization account is created
- **Update Contact:** Updates contact details (name, email, account number) when account information changes

#### Invoice Management

- **Create Invoice:** Generates an ACCREC (accounts receivable) invoice with line items in AUTHORISED status
- **Email Invoice:** Sends invoice email to the contact via Xero's email service
- **Retrieve Invoices:** Fetches invoice details including payment status and amounts
- **Update Invoices:** Synchronizes invoice data from Xero to AMS database

### Rate Limiting

The integration includes fail-fast rate limit handling:

- API calls are decorated with `@handle_rate_limit()`
- When rate limits are exceeded, `XeroRateLimitError` is raised
- Error includes retry-after information when available
- Automatic retry is not implemented; manual intervention or scheduled retry is required

### Testing

#### Mock Service

For testing without connecting to Xero, use `MockXeroBillingService`:

```python
# In your test settings
AMS_BILLING_SERVICE_CLASS = "ams.billing.providers.xero.MockXeroBillingService"
```

The mock service:

- Returns dummy data for all operations
- Does not make external API calls
- Useful for unit testing and CI/CD pipelines

#### Integration Testing

To test with the actual Xero API:

1. Use the Xero Demo Company (free for development)
2. Create a Custom Connection with demo company authorization
3. Configure credentials in `.envs/.local/django-private.ini`
4. Run the development server and test invoice creation

### Management Commands

#### Fetch Invoice Updates

Manually fetch and update invoice details from Xero:

```bash
python manage.py fetch_invoice_updates
```

This command:

- Queries invoices marked as needing updates
- Fetches latest data from Xero
- Updates local database with payment status and amounts
- Limits to 20 invoices per run to avoid rate limits

### Troubleshooting

#### Common Issues

**Authentication Errors:**

- Verify `XERO_CLIENT_ID` and `XERO_CLIENT_SECRET` are correct
- Ensure the Custom Connection is authorized in Xero
- Check that `XERO_TENANT_ID` matches your connected organization

**Webhook Verification Failed:**

- Verify `XERO_WEBHOOK_KEY` matches the key in your Xero app settings
- Check that the webhook URL is publicly accessible
- Ensure the webhook endpoint is receiving POST requests

**Rate Limit Errors:**

- Xero has API rate limits (60 requests per minute per organization)
- Implement retry logic or scheduled jobs for bulk operations
- Monitor rate limit exceptions in your logs

**Invoice Creation Fails:**

- Verify the account has an associated `XeroContact`
- Check `XERO_ACCOUNT_CODE` is valid for your Xero organization
- Ensure `XERO_CURRENCY_CODE` is supported by your Xero organization
- Verify scopes include `accounting.transactions`

**Contact Creation Fails:**

- Ensure scopes include `accounting.contacts`
- Verify contact details (name, email) are valid
- Check for duplicate contact names (AMS appends account ID to ensure uniqueness)

### Further Reading

- [Xero Custom Connections Documentation](https://developer.xero.com/documentation/guides/oauth2/custom-connections/)
- [Xero API Scopes](https://developer.xero.com/documentation/guides/oauth2/scopes/)
- [Xero Webhooks Documentation](https://developer.xero.com/documentation/guides/webhooks/overview/)
