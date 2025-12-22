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

| Variable | Description | Example | Default |
|----------|-------------|---------|---------|
| `AMS_BILLING_EMAIL_WHITELIST_REGEX` | Regex pattern to filter invoice email recipients (for testing) | `@example.com$` | None |
| `XERO_EMAIL_INVOICES` | Enable sending invoice emails via Xero (set to `False` when using Xero Demo Company) | `True` or `False` | `True` |
| `XERO_DEBUG` | Enable HTTP request/response debugging for Xero API calls | `True` or `False` | `False` |

!!! warning "Security Warning"
    Setting `XERO_DEBUG=True` will log all HTTP requests and responses, including sensitive credentials and bearer tokens. Only enable this for debugging specific API issues in isolated development environments. Never enable in production.

### Deployment Configuration

When deploying AMS with Xero integration, configure these environment variables in your deployment platform.

#### Required Environment Variables

These variables must be set for production deployments:

```bash
# Billing Provider Selection
AMS_BILLING_SERVICE_CLASS=ams.billing.providers.xero.XeroBillingService

# Xero API Credentials (from Custom Connection)
XERO_CLIENT_ID=your-client-id-here
XERO_CLIENT_SECRET=your-client-secret-here
XERO_TENANT_ID=your-tenant-id-here

# Webhook Configuration
XERO_WEBHOOK_KEY=your-webhook-key-here

# Xero Organization Settings
XERO_ACCOUNT_CODE=200
XERO_AMOUNT_TYPE=INCLUSIVE
XERO_CURRENCY_CODE=NZD
```

#### Optional Environment Variables

```bash
# Email Configuration
XERO_EMAIL_INVOICES=True  # Set to False for Xero Demo Company
AMS_BILLING_EMAIL_WHITELIST_REGEX=  # Leave empty for production

# Debugging (NEVER enable in production)
XERO_DEBUG=False
```

#### Security Best Practices

1. **Never commit credentials to version control**
2. **Use secret management** provided by your platform
3. **Rotate credentials periodically** (generate new client secrets in Xero)
4. **Restrict access** to production credentials
5. **Use different Xero apps** for development, staging, and production environments

### Webhook Configuration

AMS receives webhook notifications from Xero when invoice status changes (e.g., paid, voided).
The webhook endpoint uses HMAC-SHA256 signature verification:

**Webhook Endpoint:** `https://your-domain.com/billing/xero/webhooks/`

#### Setting Up Webhooks in Xero

1. Navigate to your Xero app in the Developer Portal
2. Go to the **Webhooks** section: `https://developer.xero.com/app/manage/app/YOUR_APP_ID/webhooks`
3. Configure the webhook:
    - **Delivery URL:** `https://your-domain.com/billing/xero/webhooks/`
    - Xero will generate a **Webhook Key** - save this as `XERO_WEBHOOK_KEY`
4. Save the configuration

#### Webhook Events Handled

Currently, AMS processes these Xero webhook events:

```python
{
    "eventCategory": "INVOICE",
    "eventType": "UPDATE",
    "tenantId": "your-tenant-id",
    "resourceId": "invoice-id-here"
}
```

**Processing Flow:**

1. Webhook received → Signature verified
2. Invoice UPDATE events extracted
3. Matching invoices marked with `update_needed=True`
4. Response sent (200 OK)
5. After response, `fetch_updated_invoice_details()` triggered
6. Invoice details fetched from Xero API
7. Local database updated with latest payment status

#### Testing Webhooks

**Local Development:**

Use ngrok or similar tool:

```bash
ngrok http 8000
```

Configure in your `.envs/.local/django-private.ini`:

```ini
NGROK_HOST=your-subdomain.ngrok-free.dev
```

Update your Xero app webhook URL:

```text
https://your-subdomain.ngrok-free.dev/billing/xero/webhooks/
```

**Manual Testing:**

Trigger webhook events by making changes in Xero:

1. Mark an invoice as paid in Xero
2. Check AMS logs for webhook receipt
3. Verify invoice status updated in AMS admin

### Architecture

#### Service Class Hierarchy

```
BillingService (ABC)
    ├── XeroBillingService
    │   └── MockXeroBillingService (for testing)
    └── MockBillingService (generic mock)
```

#### Models

**Account:**
```python
class Account(Model):
    organisation = OneToOneField(Organisation, ...)
    user = OneToOneField(User, ...)
    # Either organisation or user must be set
```

**XeroContact:**
```python
class XeroContact(Model):
    account = OneToOneField(Account, ...)
    contact_id = CharField(max_length=255)  # Xero's contact ID
```

**Invoice:**
```python
class Invoice(Model):
    account = ForeignKey(Account, ...)
    invoice_number = CharField(max_length=255, unique=True)
    billing_service_invoice_id = CharField(...)  # Xero's invoice ID
    update_needed = BooleanField(default=False)
    # Amount fields, dates, etc.
```

#### Key Service Methods

**Contact Management:**

```python
def update_user_billing_details(user: User) -> None:
    """Create or update Xero contact for a user."""

def update_organisation_billing_details(organisation: Organisation) -> None:
    """Create or update Xero contact for an organisation."""
```

**Invoice Management:**

```python
def create_invoice(
    account: Account,
    date: date,
    due_date: date,
    line_items: list[dict[str, Any]],
    reference: str,
) -> Invoice:
    """Create invoice in Xero and local DB."""

def email_invoice(invoice: Invoice) -> None:
    """Send invoice email via Xero."""

def update_invoices(billing_service_invoice_ids: list[str]) -> None:
    """Fetch latest invoice data from Xero."""

def get_invoice_url(invoice: Invoice) -> str | None:
    """Get customer-facing online invoice URL."""
```

### Rate Limiting

Xero enforces API rate limits to prevent abuse and ensure service stability. Understanding and handling these limits is crucial for reliable operation.

#### Xero Rate Limit Details

- **Rate Limit:** 60 requests per minute per organization
- **Limit Window:** Rolling 60-second window
- **Headers:** Xero returns rate limit information in response headers:
    - `X-Rate-Limit-Limit`: Maximum requests allowed (60)
    - `X-Rate-Limit-Remaining`: Requests remaining in current window
    - `X-Rate-Limit-Problem`: Returned when limit is exceeded

#### AMS Rate Limit Handling

The integration uses a fail-fast approach with the `@handle_rate_limit()` decorator:

```python
from ams.billing.providers.xero.rate_limiting import handle_rate_limit

@handle_rate_limit()
def _create_xero_invoice(self, ...):
    # API call here
    pass
```

**Behavior:**

1. API calls are wrapped with rate limit detection
2. When rate limits are exceeded (HTTP 429), `XeroRateLimitError` is raised
3. The error includes `retry_after` seconds when available from Xero's response
4. **No automatic retry** - operations fail immediately to prevent cascading delays

#### Handling Rate Limit Errors

**During Webhook Processing:**

- Webhook handlers mark invoices as `update_needed=True` instead of fetching immediately
- The `fetch_invoice_updates` command processes updates in batches
- Limits processing to 30 invoices per run to avoid hitting rate limits

**During Bulk Operations:**

If performing bulk operations (e.g., importing many members):

```python
from ams.billing.providers.xero.rate_limiting import XeroRateLimitError
import time

for member in members:
    try:
        billing_service.update_user_billing_details(member)
    except XeroRateLimitError as e:
        # Wait for the retry_after period
        time.sleep(e.retry_after or 60)
        # Retry or defer to next run
        continue
```

**Recommended Strategies:**

1. **Batch Processing:** Process records in small batches with delays between batches
2. **Scheduled Jobs:** Spread bulk operations across multiple cron runs
3. **Queue-based Processing:** Use a task queue (e.g., Celery) with rate limiting
4. **Monitor Remaining Requests:** Check `X-Rate-Limit-Remaining` header to throttle proactively

#### Rate Limit Monitoring

Log rate limit errors to track API usage patterns:

```python
import logging
logger = logging.getLogger(__name__)

try:
    billing_service.create_invoice(...)
except XeroRateLimitError as e:
    logger.warning(
        "Xero rate limit exceeded. Retry after %s seconds",
        e.retry_after
    )
```

Configure Sentry or your monitoring system to alert on rate limit errors for proactive response.

### Testing

#### Unit Tests

Run billing tests:

```bash
pytest ams/billing/tests/
```

Key test files:

- `test_invoice_model.py` - Invoice model tests
- `test_account_model.py` - Account model tests
- `test_fetch_invoice_updates_command.py` - Management command tests

#### Mock Service for Testing

For testing without connecting to Xero, use `MockXeroBillingService`:

```python
# In config/settings/test.py
BILLING_SERVICE_CLASS = "ams.billing.providers.xero.MockXeroBillingService"
```

The mock service:

- Returns dummy data for all operations
- Does not make external API calls
- Useful for unit testing and CI/CD pipelines
- Creates predictable invoice IDs and numbers

### Management Commands

#### fetch_invoice_updates

Manually fetch and update invoice details from Xero:

```bash
python manage.py fetch_invoice_updates
```

**Purpose:**

- Queries local invoices marked with `update_needed=True`
- Fetches latest data from Xero API (payment status, amounts, dates)
- Updates local database with current information
- Marks invoices as no longer needing updates

**Behavior:**

- Processes up to 30 invoices per run (to avoid rate limits)
- Only works with `XeroBillingService` (skips mock services)
- Logs progress and results to stdout
- Raises exceptions for debugging when called manually

**When to Use:**

- After webhook outages or delivery failures
- During initial data migration from Xero
- For manual invoice status verification
- In scheduled cron jobs to catch missed webhook events

### Troubleshooting

#### Authentication Issues

**Symptom:** "Invalid credentials" or "Unauthorized" errors

**Possible Causes:**

- Incorrect `XERO_CLIENT_ID` or `XERO_CLIENT_SECRET`
- Custom Connection not authorized or authorization expired
- Incorrect `XERO_TENANT_ID`

**Solutions:**

1. Verify credentials in Xero Developer Portal match environment variables
2. Check Custom Connection is still authorized (hasn't been revoked)
3. Confirm `XERO_TENANT_ID` matches the connected organization
4. Try regenerating client secret and updating `XERO_CLIENT_SECRET`

#### Webhook Verification Failures

**Symptom:** Webhooks return 401 Unauthorized

**Possible Causes:**

- Incorrect `XERO_WEBHOOK_KEY`
- Webhook key changed in Xero but not updated in AMS
- Request not actually from Xero (spoofing attempt)

**Solutions:**

1. Verify `XERO_WEBHOOK_KEY` matches the key shown in Xero Developer Portal
2. Check Xero's webhook delivery logs for signature details
3. Test webhook signature locally

#### Rate Limit Errors

**Symptom:** `XeroRateLimitError` raised during operations

**Cause:** Exceeded Xero's 60 requests per minute limit

**Solutions:**

1. **Immediate:** Wait for the `retry_after` period before retrying
2. **Short-term:** Reduce concurrent operations or add delays between requests
3. **Long-term:** Implement queueing system with rate limiting

#### Invoice Creation Failures

**Symptom:** Invoice creation fails or returns errors

**Possible Causes:**

1. Account missing associated `XeroContact`
2. Invalid `XERO_ACCOUNT_CODE` for the organization
3. Unsupported `XERO_CURRENCY_CODE`
4. Missing `accounting.transactions` scope
5. Invalid line item data

#### Contact Creation or Update Failures

**Symptom:** Contact operations fail

**Possible Causes:**

- Missing `accounting.contacts` scope
- Duplicate contact name (shouldn't happen with UUID prefix)
- Invalid email address format

#### Invoice Status Not Updating

**Symptom:** Invoice paid in Xero but still shows as unpaid in AMS

**Possible Causes:**

1. Webhook not configured or failing
2. `fetch_invoice_updates` command not running
3. `update_needed` flag not being set

#### Email Invoices Not Sending

**Symptom:** Invoices created but emails not received

**Possible Causes:**

1. `XERO_EMAIL_INVOICES=False` in settings
2. Using Xero Demo Company (emails disabled)
3. Invalid contact email address
4. `AMS_BILLING_EMAIL_WHITELIST_REGEX` filtering recipient

#### Getting Help

If issues persist:

1. **Check Xero API Status:** [status.xero.com](https://status.xero.com)
2. **Review Xero API Logs:** Developer Portal → Your App → API Logs
3. **Enable Debug Logging:** Set `XERO_DEBUG=True` (development only)
4. **Check Django Logs:** Review application logs for detailed error messages
5. **Consult Xero Documentation:** [developer.xero.com](https://developer.xero.com)
6. **Contact Support:** Reach out to your AMS implementation team with:
    - Error messages (sanitize any credentials)
    - Steps to reproduce
    - Django and Xero API logs
    - Environment details (development/staging/production)

### Further Reading

- [Xero Custom Connections Documentation](https://developer.xero.com/documentation/guides/oauth2/custom-connections/)
- [Xero API Scopes](https://developer.xero.com/documentation/guides/oauth2/scopes/)
- [Xero Webhooks Documentation](https://developer.xero.com/documentation/guides/webhooks/overview/)
