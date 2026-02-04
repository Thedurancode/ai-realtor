# MCP Integration Guide for AI Realtor

## What is MCP?

**Model Context Protocol (MCP)** allows your AI Realtor system to connect to external services and tools through standardized servers.

---

## Available MCP Servers

### 1. Context7 MCP (Documentation)

**Purpose:** Get up-to-date documentation for any library

**Available Tools:**
- `resolve-library-id` - Find library documentation
- `query-docs` - Search documentation

**Example Use Cases:**
```
"Show me the latest FastAPI documentation for async routes"
"How do I use SQLAlchemy relationships in 2026?"
"What's the new Resend API syntax?"
```

---

### 2. Stripe MCP (Payments)

**Purpose:** Process payments for real estate services

**Available Tools:**
- `create_customer` - Create Stripe customer
- `create_product` - Create service product
- `create_price` - Set pricing
- `create_invoice` - Generate invoices
- `create_payment_link` - Payment links
- `list_customers` - View customers
- `create_refund` - Process refunds

**Example Integration:**

#### Charge for Skip Trace Services
```python
# 1. Create Product
product = mcp__MCP_DOCKER__create_product(
    name="Skip Trace Report",
    description="Property owner contact information"
)

# 2. Set Price
price = mcp__MCP_DOCKER__create_price(
    product=product.id,
    unit_amount=2500,  # $25.00
    currency="usd"
)

# 3. Create Payment Link
payment_link = mcp__MCP_DOCKER__create_payment_link(
    price=price.id,
    quantity=1
)
# → Returns: payment URL
```

#### Contract Signing Fees
```python
# Charge $50 for contract processing
contract_product = create_product(
    name="Contract Processing Fee",
    description="DocuSeal contract creation and sending"
)

contract_price = create_price(
    product=contract_product.id,
    unit_amount=5000,  # $50.00
    currency="usd"
)
```

#### Subscription Plans
```python
# Premium plan with unlimited skip traces
premium_product = create_product(
    name="Premium Real Estate Plan",
    description="Unlimited skip traces, contracts, and email notifications"
)

monthly_price = create_price(
    product=premium_product.id,
    unit_amount=9900,  # $99/month
    currency="usd",
    recurring={"interval": "month"}
)
```

---

### 3. Happy MCP (Chat Management)

**Purpose:** Organize conversation history

**Available Tools:**
- `change_title` - Update chat title

**Example:**
```python
mcp__happy__change_title(
    title="312 Eisler Ln - Skip Trace & Contract"
)
```

---

## MCP Integration Architecture

```
┌─────────────────────────────────────────┐
│         AI Realtor System               │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │     FastAPI Backend             │   │
│  │  • Property Management          │   │
│  │  • Skip Tracing                 │   │
│  │  • Contract Sending             │   │
│  └─────────────────────────────────┘   │
│              ↕                          │
│  ┌─────────────────────────────────┐   │
│  │     MCP Servers                 │   │
│  │                                 │   │
│  │  • Context7 (Docs)              │   │
│  │  • Stripe (Payments)            │   │
│  │  • Happy (Organization)         │   │
│  └─────────────────────────────────┘   │
│              ↕                          │
│  ┌─────────────────────────────────┐   │
│  │   External Services             │   │
│  │                                 │   │
│  │  • Google Places API            │   │
│  │  • RapidAPI Skip Trace          │   │
│  │  • DocuSeal (Self-hosted)       │   │
│  │  • Resend Email                 │   │
│  │  • Stripe Payments              │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

---

## Example: Complete Paid Skip Trace Flow

### Step 1: Customer Requests Skip Trace
```bash
POST /skip-trace/property/2/paid
```

### Step 2: Create Stripe Payment
```python
# Create customer
customer = mcp__MCP_DOCKER__create_customer(
    name="Real Estate Agent",
    email="agent@example.com"
)

# Create invoice
invoice = mcp__MCP_DOCKER__create_invoice(
    customer=customer.id,
    days_until_due=7
)

# Add skip trace service
invoice_item = mcp__MCP_DOCKER__create_invoice_item(
    customer=customer.id,
    price=skip_trace_price_id,
    invoice=invoice.id
)

# Finalize invoice
finalized = mcp__MCP_DOCKER__finalize_invoice(
    invoice=invoice.id
)
```

### Step 3: After Payment, Run Skip Trace
```python
# Verify payment received
payment_intents = mcp__MCP_DOCKER__list_payment_intents(
    customer=customer.id
)

if payment_intents[0]['status'] == 'succeeded':
    # Run skip trace
    result = await skip_trace_service.skip_trace(
        address=property.address,
        city=property.city,
        state=property.state,
        zip_code=property.zip_code
    )
    # Return results
```

---

## Revenue Opportunities with MCP + Stripe

### 1. **Pay-Per-Skip-Trace**
- Charge $25 per property skip trace
- Automated billing via Stripe MCP
- Instant access after payment

### 2. **Contract Processing Fees**
- $50 per contract sent
- Includes DocuSeal + Resend emails
- Professional service fee

### 3. **Subscription Tiers**

**Basic Plan - $29/month**
- 10 skip traces/month
- 20 contracts/month
- Standard email templates

**Pro Plan - $99/month**
- Unlimited skip traces
- Unlimited contracts
- Custom email templates
- Priority support

**Enterprise - $299/month**
- Everything in Pro
- API access
- Webhook integrations
- White-label option

### 4. **Premium Features**
- **Advanced Skip Trace** - $50 (includes phone verification)
- **Rush Contract** - $20 (24-hour processing)
- **Email Templates** - $10/template
- **Custom Branding** - $100 one-time

---

## How to Add Stripe Payments

### Step 1: Create Stripe Account
1. Go to https://stripe.com
2. Sign up for account
3. Get API keys from dashboard

### Step 2: Configure MCP Stripe Server
(Already configured via Docker MCP)

### Step 3: Create Products
```python
# Skip trace product
skip_trace = mcp__MCP_DOCKER__create_product(
    name="Property Skip Trace",
    description="Find property owner contact information"
)

skip_trace_price = mcp__MCP_DOCKER__create_price(
    product=skip_trace.id,
    unit_amount=2500,
    currency="usd"
)
```

### Step 4: Add Payment Endpoint
```python
@router.post("/skip-trace/property/{property_id}/purchase")
async def purchase_skip_trace(property_id: int):
    # Create payment link
    payment_link = mcp__MCP_DOCKER__create_payment_link(
        price=skip_trace_price_id,
        quantity=1,
        redirect_url=f"https://yourdomain.com/skip-trace/{property_id}/view"
    )

    return {
        "payment_url": payment_link.url,
        "amount": "$25.00"
    }
```

### Step 5: Verify Payment Webhook
```python
@router.post("/webhooks/stripe")
async def stripe_webhook(payload: dict):
    if payload['type'] == 'payment_intent.succeeded':
        # Run skip trace
        # Send results to customer
        pass
```

---

## MCP Advantages

### 1. **Standardized Integration**
- No custom API clients needed
- Consistent interface across services
- Easy to swap providers

### 2. **Real-time Access**
- Live data from services
- Up-to-date documentation
- Current pricing information

### 3. **Simplified Development**
- Less code to maintain
- Built-in error handling
- Automatic retries

### 4. **Enhanced Capabilities**
- Payment processing
- Documentation lookup
- Service orchestration

---

## Future MCP Integrations

### Potential MCP Servers to Add:

**1. Gmail MCP**
- Send/receive emails
- Track responses
- Manage inbox

**2. Calendar MCP**
- Schedule property viewings
- Set reminders for contract deadlines
- Sync with Google Calendar

**3. CRM MCP**
- HubSpot integration
- Salesforce sync
- Contact management

**4. SMS MCP**
- Twilio integration
- SMS notifications
- Two-way messaging

**5. Storage MCP**
- AWS S3 for documents
- Document versioning
- Secure file sharing

**6. Analytics MCP**
- Track usage metrics
- Generate reports
- Business intelligence

---

## Current System + MCP Summary

**Your AI Realtor now supports:**

✅ **Direct API Integrations:**
- Google Places (Property enrichment)
- RapidAPI (Skip tracing)
- DocuSeal (Contract signing)
- Resend (Email notifications)

✅ **MCP Server Integrations:**
- Context7 (Documentation)
- Stripe (Payments) - Available
- Happy (Chat management)

✅ **Ready for Expansion:**
- Add payment processing in minutes
- Scale with subscription plans
- Monetize premium features

---

## Get Started with MCP

### Test Stripe MCP (Already Available!)

```python
# List your Stripe products
mcp__MCP_DOCKER__list_products(limit=10)

# Create test customer
mcp__MCP_DOCKER__create_customer(
    name="Test Customer",
    email="test@example.com"
)

# Check balance
mcp__MCP_DOCKER__retrieve_balance()
```

### Test Context7 MCP

```python
# Get FastAPI docs
mcp__context7__resolve_library_id(
    libraryName="fastapi",
    query="async database sessions"
)

mcp__context7__query_docs(
    libraryId="/tiangolo/fastapi",
    query="How to use async database sessions with SQLAlchemy"
)
```

---

**MCP makes your AI Realtor even more powerful by connecting to external services through standardized protocols!** 🚀
