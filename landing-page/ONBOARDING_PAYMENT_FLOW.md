# Onboarding Payment Flow - Technical Documentation

## Overview

The onboarding flow has been updated to include:
1. **Onboarding wizard** - Collect agent configuration
2. **Pricing selection** - User selects Starter ($99), Professional ($299), or Enterprise ($500/year)
3. **Stripe payment** - Secure payment processing
4. **Magic link generation** - User receives a unique tracking link (expires in 7 days) to monitor installation status

---

## Frontend Flow

### Step 1: Complete Onboarding Wizard
User fills out the onboarding form with their agent configuration.

**Endpoint:** `POST /onboarding/validate`
**Purpose:** Validates onboarding data without creating the agent yet
**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "email": "john@example.com",
  "phone": "+15551234567",
  "business_name": "Smith Realty",
  "assistant_name": "Smith Assistant",
  "assistant_style": "Professional & Formal",
  "schedule": {...},
  "branding": {...},
  "voice_settings": {...},
  "calendar_enabled": true,
  "google_places_enabled": false
}
```

**Response:**
```json
{
  "valid": true,
  "message": "Onboarding data validated"
}
```

### Step 2: Select Pricing Plan
User sees pricing modal with 3 options:
- **Starter** - $99 (one-time, self-hosted)
- **Professional** - $299 (one-time, installation support)
- **Enterprise** - $500/year (fully managed)

### Step 3: Process Payment
User clicks "Select [Plan]" which triggers payment flow.

**Endpoint:** `POST /onboarding/create-agent-and-payment`
**Purpose:** Creates agent record AND initiates Stripe Checkout session
**Request Body:**
```json
{
  "onboarding_data": {
    "first_name": "John",
    "last_name": "Smith",
    "email": "john@example.com",
    // ... all onboarding fields
  },
  "plan": "professional",
  "price": 299
}
```

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/...",
  "session_id": "cs_test_abc123"
}
```

### Step 4: Redirect to Stripe
User is redirected to Stripe Checkout to complete payment.

### Step 5: Stripe Webhook/Redirect
After payment, Stripe redirects back to onboarding page with:
```
/onboarding.html?session_id=cs_test_abc123&success=true
```

### Step 6: Generate Magic Link
Frontend detects payment success and calls backend.

**Endpoint:** `GET /onboarding/payment-success?session_id={session_id}`
**Purpose:** Confirm payment and generate magic link
**Response:**
```json
{
  "magic_link": "https://ai-realtor.fly.dev/install/track/abc123xyz789",
  "expires_at": "2026-03-06T10:00:00Z",
  "agent_id": 123,
  "access_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### Step 7: Display Magic Link
User sees success modal with:
- ✅ Payment confirmation
- ⚠️ Security warning (DO NOT SHARE LINK)
- 🔗 Magic link input with copy button
- ⏰ Expiry date (7 days)
- 📋 Features list (track installation, view status, download files)
- 🔗 "Open Tracking Link" button
- 🔖 "Bookmark This Page" button

---

## Backend API Endpoints Required

### 1. POST /onboarding/validate
Validate onboarding data without creating agent.

```python
@router.post("/onboarding/validate")
async def validate_onboarding(data: dict, db: Session = Depends(get_db)):
    """
    Validate onboarding data.

    Checks:
    - Email format and uniqueness
    - Phone number format
    - Required fields
    - Business card OCR if provided
    """
    # Validate email
    if not re.match(r"[^@]+@[^@]+\.[^@]+", data.get("email", "")):
        raise HTTPException(400, "Invalid email format")

    # Check if email already exists
    existing = db.query(Agent).filter(Agent.email == data["email"]).first()
    if existing:
        raise HTTPException(400, "An account with this email already exists")

    # Validate required fields
    required_fields = ["first_name", "last_name", "email", "phone", "business_name"]
    for field in required_fields:
        if not data.get(field):
            raise HTTPException(400, f"Missing required field: {field}")

    return {"valid": True, "message": "Onboarding data validated"}
```

### 2. POST /onboarding/create-agent-and-payment
Create agent AND initiate Stripe Checkout.

```python
import stripe
import uuid
from datetime import datetime, timedelta

stripe.api_key = "sk_live_YOUR_SECRET_KEY"

@router.post("/onboarding/create-agent-and-payment")
async def create_agent_and_payment(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Create agent record and initiate Stripe Checkout.
    """
    onboarding_data = request.get("onboarding_data")
    plan = request.get("plan")
    price = request.get("price")

    # Check if agent already exists
    existing = db.query(Agent).filter(Agent.email == onboarding_data["email"]).first()
    if existing:
        raise HTTPException(400, "Account already exists")

    # Create agent record
    agent = Agent(
        email=onboarding_data["email"],
        first_name=onboarding_data["first_name"],
        last_name=onboarding_data["last_name"],
        phone=onboarding_data["phone"],
        business_name=onboarding_data["business_name"],
        assistant_name=onboarding_data.get("assistant_name"),
        assistant_style=onboarding_data.get("assistant_style"),
        schedule=onboarding_data.get("schedule"),
        branding_colors=onboarding_data.get("branding"),
        voice_settings=onboarding_data.get("voice_settings"),
        calendar_enabled=onboarding_data.get("calendar_enabled"),
        google_places_enabled=onboarding_data.get("google_places_enabled"),
        plan=plan,
        payment_status="pending",
        created_at=datetime.utcnow()
    )

    db.add(agent)
    db.commit()
    db.refresh(agent)

    # Create Stripe Checkout Session
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'AgentClaw AI - {plan.capitalize()} Plan',
                        'description': f'One-time payment for {plan} plan' if plan != 'enterprise' else 'Annual enterprise plan',
                    },
                    'unit_amount': price * 100,  # Convert to cents
                },
                'quantity': 1,
            }],
            mode='payment' if plan != 'enterprise' else 'subscription',
            success_url=f'https://your-domain.com/landing-page/onboarding.html?session_id={{CHECKOUT_SESSION_ID}}&success=true',
            cancel_url=f'https://your-domain.com/landing-page/onboarding.html?success=false',
            customer_email=onboarding_data["email"],
            metadata={
                'agent_id': str(agent.id),
                'plan': plan,
                'price': str(price)
            }
        )

        # Store session ID with agent
        agent.stripe_session_id = session.id
        db.commit()

        return {
            "checkout_url": session.url,
            "session_id": session.id
        }

    except Exception as e:
        # Rollback agent creation on Stripe error
        db.delete(agent)
        db.commit()
        raise HTTPException(500, f"Failed to create payment session: {str(e)}")
```

### 3. GET /onboarding/payment-success
Confirm payment and generate magic link.

```python
import secrets
from datetime import datetime, timedelta

@router.get("/onboarding/payment-success")
async def payment_success(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Confirm Stripe payment and generate magic link.
    """
    # Retrieve Stripe session
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        raise HTTPException(400, "Invalid session ID")

    # Verify payment status
    if session.payment_status != 'paid':
        raise HTTPException(400, "Payment not completed")

    # Get agent from metadata
    agent_id = int(session.metadata.get('agent_id'))
    agent = db.query(Agent).filter(Agent.id == agent_id).first()

    if not agent:
        raise HTTPException(404, "Agent not found")

    # Update agent payment status
    agent.payment_status = "paid"
    agent.paid_at = datetime.utcnow()

    # Generate magic link token
    magic_token = secrets.token_urlsafe(32)

    # Set expiry (7 days from now)
    expires_at = datetime.utcnow() + timedelta(days=7)

    # Store magic link token
    agent.magic_link_token = magic_token
    agent.magic_link_expires_at = expires_at

    db.commit()

    # Generate magic link URL
    magic_link = f"{settings.BASE_URL}/install/track/{magic_token}"

    # Send welcome email with magic link
    send_welcome_email(agent.email, magic_link)

    return {
        "magic_link": magic_link,
        "expires_at": expires_at.isoformat(),
        "agent_id": agent.id
    }

def send_welcome_email(email: str, magic_link: str):
    """
    Send welcome email with magic link.
    """
    # Use your email service (SendGrid, Mailgun, etc.)
    pass
```

### 4. GET /install/track/{magic_token}
Magic link endpoint - shows installation status without login.

```python
from fastapi import Query

@router.get("/install/track/{magic_token}")
async def track_installation(
    magic_token: str,
    db: Session = Depends(get_db)
):
    """
    Installation tracking page (magic link).
    No authentication required - token grants access.
    """
    # Find agent by magic token
    agent = db.query(Agent).filter(
        Agent.magic_link_token == magic_token
    ).first()

    if not agent:
        raise HTTPException(404, "Invalid tracking link")

    # Check if token is expired
    if agent.magic_link_expires_at and agent.magic_link_expires_at < datetime.utcnow():
        raise HTTPException(401, "Tracking link has expired")

    # Return installation status
    return {
        "agent": {
            "id": agent.id,
            "name": agent.assistant_name,
            "email": agent.email,
            "created_at": agent.created_at.isoformat(),
            "payment_status": agent.payment_status,
            "plan": agent.plan
        },
        "installation": {
            "status": agent.installation_status,  # pending, installing, complete, error
            "progress": agent.installation_progress,  # 0-100
            "logs": agent.installation_logs,
            "completed_at": agent.installation_completed_at
        },
        "download_links": {
            "documentation": f"{settings.BASE_URL}/docs",
            "github": "https://github.com/Thedurancode/ai-realtor",
            "docker_compose": f"{settings.BASE_URL}/api/docker-compose?token={magic_token}"
        }
    }
```

---

## Database Schema Changes

Add these fields to the `agents` table:

```sql
ALTER TABLE agents ADD COLUMN IF NOT EXISTS plan VARCHAR(50);
ALTER TABLE agents ADD COLUMN IF NOT EXISTS payment_status VARCHAR(50) DEFAULT 'pending';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS paid_at TIMESTAMP;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS stripe_session_id VARCHAR(255);
ALTER TABLE agents ADD COLUMN IF NOT EXISTS magic_link_token TEXT UNIQUE;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS magic_link_expires_at TIMESTAMP;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS installation_status VARCHAR(50) DEFAULT 'pending';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS installation_progress INTEGER DEFAULT 0;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS installation_logs TEXT;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS installation_completed_at TIMESTAMP;
```

---

## Stripe Webhook Handler

Create webhook endpoint to handle Stripe events:

```python
@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhooks for payment events.
    """
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(400, "Invalid signature")

    # Handle checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Get agent from metadata
        agent_id = int(session.metadata.get('agent_id'))
        agent = db.query(Agent).filter(Agent.id == agent_id).first()

        if agent:
            agent.payment_status = "paid"
            agent.paid_at = datetime.utcnow()
            db.commit()

            # Start installation process (background task)
            initiate_installation(agent.id)

    return {"status": "success"}

def initiate_installation(agent_id: int):
    """
    Start background installation process.
    This could trigger a Celery task, background worker, etc.
    """
    # Implementation depends on your installation process
    pass
```

---

## Security Considerations

### Magic Link Security
1. **Token Generation**: Use `secrets.token_urlsafe(32)` for cryptographically secure tokens
2. **Expiry**: Enforce 7-day expiry strictly
3. **Single Use**: Consider marking token as used after first access
4. **HTTPS Only**: Only serve magic links over HTTPS
5. **Rate Limiting**: Limit magic link access attempts

### Payment Security
1. **Webhook Signature Verification**: Always verify Stripe webhook signatures
2. **Idempotency**: Handle duplicate webhook events
3. **Amount Verification**: Verify payment amount matches plan price
4. **Metadata Validation**: Validate agent_id exists and belongs to correct email

### Data Privacy
1. **No Card Storage**: Never store card details (Stripe handles this)
2. **Email Verification**: Confirm email ownership before sending magic link
3. **Minimal Data**: Only collect necessary onboarding data

---

## Testing Checklist

- [ ] Complete onboarding wizard
- [ ] Validate onboarding data API
- [ ] Select Starter plan - see correct price
- [ ] Select Professional plan - see correct price
- [ ] Select Enterprise plan - see correct price
- [ ] Stripe checkout opens correctly
- [ ] Complete test payment with Stripe test card (4242 4242 4242 4242)
- [ ] Redirect back to onboarding page with session_id
- [ ] Magic link generated successfully
- [ ] Magic link expires after 7 days
- [ ] Magic link shows correct installation status
- [ ] Warning message displayed (DO NOT SHARE)
- [ ] Copy button works
- [ ] "Open Tracking Link" button opens in new tab
- [ ] Welcome email sent with magic link
- [ ] Handle payment cancellation
- [ ] Handle payment failure

---

## Environment Variables

```bash
# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Application
BASE_URL=https://ai-realtor.fly.dev

# Email (for welcome emails)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=...
```

---

## Troubleshooting

### Issue: Magic link not generated
**Solution**: Check Stripe webhook is configured correctly and `session_id` matches

### Issue: Magic link shows "expired"
**Solution**: Verify `magic_link_expires_at` is set 7 days in future, check timezone handling

### Issue: Payment not completing
**Solution**: Check Stripe secret key, verify webhook URL is reachable

### Issue: Agent not created
**Solution**: Check database logs, verify email uniqueness constraint

---

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)
