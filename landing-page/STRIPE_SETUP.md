# Stripe Payment Integration Setup Guide

This guide will help you configure Stripe payments for the AgentClaw API landing page.

## Prerequisites

1. A Stripe account (sign up at https://stripe.com)
2. Your Stripe publishable key (starts with `pk_live_` or `pk_test_` for testing)

## Setup Options

You have two options for accepting payments:

### Option 1: Stripe Payment Links (Recommended - Easiest)

This is the simplest method - create payment links in your Stripe Dashboard and paste them into the code.

#### Step 1: Create Payment Links in Stripe Dashboard

1. Log into your Stripe Dashboard: https://dashboard.stripe.com
2. Navigate to **Products** → **Payment links**
3. Click **+ Add payment link**

For each pricing tier, create a payment link:

#### Starter Plan ($99 one-time)
- **Name**: AgentClaw API - Starter Plan
- **Price**: $99 USD
- **Payment type**: One-time
- **Description**: Self-hosted AgentClaw API - Complete platform access with 585+ endpoints and 262 voice commands

#### Professional Plan ($299 one-time)
- **Name**: AgentClaw API - Professional Plan
- **Price**: $299 USD
- **Payment type**: One-time
- **Description**: Self-hosted with installation support and email assistance

#### Enterprise Plan ($500/year)
- **Name**: AgentClaw API - Enterprise Plan
- **Price**: $500 USD
- **Payment type**: Recurring (yearly)
- **Description**: Fully managed hosting, priority support, and 99.9% uptime SLA

#### Step 2: Update the JavaScript Code

Open `landing-page/index.html` and find the `redirectToStripe()` function around line 2045. Replace the placeholder URLs with your actual Stripe Payment Links:

```javascript
function redirectToStripe(plan, price) {
    const paymentLinks = {
        starter: 'https://buy.stripe.com/PASTE_YOUR_STARTER_LINK_HERE',
        professional: 'https://buy.stripe.com/PASTE_YOUR_PROFESSIONAL_LINK_HERE',
        enterprise: 'https://buy.stripe.com/PASTE_YOUR_ENTERPRISE_LINK_HERE'
    };

    const url = paymentLinks[plan];
    // ... rest of the function
}
```

#### Step 3: Update Your Stripe Publishable Key

Find the `STRIPE_PUBLISHABLE_KEY` constant around line 1979 and replace it with your actual key:

```javascript
const STRIPE_PUBLISHABLE_KEY = 'pk_live_YOUR_ACTUAL_KEY_HERE';
```

**For testing**, use your test key:
```javascript
const STRIPE_PUBLISHABLE_KEY = 'pk_test_YOUR_TEST_KEY_HERE';
```

---

### Option 2: Stripe Checkout with Backend API (Advanced)

This option requires creating a backend endpoint to create Stripe Checkout Sessions programmatically. This gives you more control over the checkout process.

#### Step 1: Create a Backend Endpoint

In your FastAPI application (`app/main.py`), add a Stripe checkout endpoint:

```python
import stripe
from fastapi import HTTPException
from pydantic import BaseModel

stripe.api_key = "sk_your_secret_key_here"  # From Stripe Dashboard

class CheckoutRequest(BaseModel):
    plan: str
    price: int

@app.post("/api/create-checkout-session")
async def create_checkout_session(request: CheckoutRequest):
    """
    Create a Stripe Checkout Session for the given plan
    """
    plan_configs = {
        "starter": {
            "name": "AgentClaw API - Starter Plan",
            "price": 9900,  # $99 in cents
            "description": "Self-hosted AgentClaw API - Complete platform access"
        },
        "professional": {
            "name": "AgentClaw API - Professional Plan",
            "price": 29900,  # $299 in cents
            "description": "Self-hosted with installation support"
        },
        "enterprise": {
            "name": "AgentClaw API - Enterprise Plan",
            "price": 50000,  # $500 in cents
            "description": "Fully managed hosting and support"
        }
    }

    if request.plan not in plan_configs:
        raise HTTPException(status_code=400, detail="Invalid plan")

    config = plan_configs[request.plan]

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': config['name'],
                        'description': config['description'],
                    },
                    'unit_amount': config['price'],
                },
                'quantity': 1,
            }],
            mode='payment' if request.plan != 'enterprise' else 'subscription',
            success_url='https://your-domain.com/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://your-domain.com/pricing?cancelled=true',
        )

        return {"url": session.url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### Step 2: Update the Frontend JavaScript

Modify the `handleStripeCheckout()` function in `landing-page/index.html`:

```javascript
async function handleStripeCheckout(plan, price) {
    const button = event.target.closest('.stripe-checkout-button');
    const originalText = button.innerHTML;
    button.innerHTML = 'Processing...';
    button.disabled = true;

    try {
        // Call your backend endpoint
        const response = await fetch('https://your-api.com/api/create-checkout-session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ plan, price }),
        });

        const session = await response.json();

        // Redirect to Stripe Checkout
        if (session.url) {
            window.location.href = session.url;
        } else {
            throw new Error('No checkout URL returned');
        }

    } catch (error) {
        console.error('Checkout error:', error);
        button.innerHTML = originalText;
        button.disabled = false;
        alert('Payment initialization failed. Please try again.');
    }
}
```

#### Step 3: Add Success/Cancel Pages

Create `success.html` and add this to `pricing.html`:

```html
<!-- Add to pricing.html for cancelled payments -->
<div id="cancelled-message" style="display:none;">
    <p>Payment cancelled. You can try again anytime.</p>
</div>

<script>
    // Check if payment was cancelled
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('cancelled') === 'true') {
        document.getElementById('cancelled-message').style.display = 'block';
    }
</script>
```

---

## Testing Your Setup

### Test Mode

1. Use your test publishable key (`pk_test_...`)
2. Use Stripe test card numbers:
   - **Success**: `4242 4242 4242 4242`
   - **Decline**: `4000 0000 0000 0002`
   - **Requires 3D Secure**: `4000 0025 0000 3155`
   - **Expiration**: Any future date (e.g., 12/34)
   - **CVC**: Any 3 digits

### Go Live

1. Switch to your live publishable key (`pk_live_...`)
2. Update your backend to use live secret key (`sk_live_...`)
3. Complete Stripe's account activation requirements:
   - Business information
   - Bank account for payouts
   - Verify your email

---

## Post-Payment Setup

After successful payment, you'll need to:

1. **Deliver the product** - Send download link or repository access
2. **Provide onboarding** - Schedule setup call for Professional/Enterprise plans
3. **Grant access** - Add customer to your private GitHub repo (if applicable)

You can use Stripe Webhooks to automate this:

```python
@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            customer_email = session['customer_details']['email']
            plan = session['metadata'].get('plan')

            # Send welcome email with download link
            # Add to GitHub repo
            # Schedule onboarding call if Professional/Enterprise

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": "success"}
```

---

## Security Notes

1. **Never commit** your Stripe secret keys to Git
2. Use environment variables for all keys
3. Always use HTTPS in production
4. Verify webhook signatures to prevent fraud
5. Keep your Stripe API keys in `.env` file:
   ```
   STRIPE_PUBLISHABLE_KEY=pk_live_...
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```

---

## Troubleshooting

### "Stripe not initialized" error
- Make sure your `STRIPE_PUBLISHABLE_KEY` is set correctly
- Check that the key starts with `pk_` (not `sk_`)

### "Payment Links not yet configured" alert
- Create Payment Links in your Stripe Dashboard
- Update the URLs in the `redirectToStripe()` function

### Webhook not firing
- Verify your webhook endpoint URL is correct
- Check that the webhook secret matches
- Ensure your server is publicly accessible (not localhost)

---

## Need Help?

- Stripe Documentation: https://stripe.com/docs
- Stripe Support: https://support.stripe.com
- Payment Links Guide: https://stripe.com/docs/payment-links

---

## Quick Checklist

- [ ] Create Stripe account
- [ ] Create 3 products (Starter, Professional, Enterprise)
- [ ] Create Payment Links for each product
- [ ] Update `STRIPE_PUBLISHABLE_KEY` in index.html
- [ ] Update `paymentLinks` URLs in `redirectToStripe()` function
- [ ] Test with Stripe test cards
- [ ] Set up webhook for automated fulfillment
- [ ] Switch to live mode
- [ ] Verify payouts are configured

---

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)
