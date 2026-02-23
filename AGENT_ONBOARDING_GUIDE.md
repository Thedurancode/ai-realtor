# 🎓 Agent Onboarding System — Complete Guide

## Overview

When agents first sign up, they're asked a series of questions to personalize their AI experience. All answers are stored in the **Memory Graph** and used to provide tailored assistance.

---

## 📋 Onboarding Questions (18 Questions)

### **Category 1: Basic Info (4 questions)**

1. **What's your full name?** ✅ Required
   - Type: Text
   - Stores: Agent identity in memory

2. **What's your email address?** ✅ Required
   - Type: Text
   - Stores: Contact info

3. **What's your brokerage or company name?** ✅ Required
   - Type: Text
   - Stores: Business affiliation

4. **What's your real estate license number?**
   - Type: Text
   - Stores: Professional credentials

---

### **Category 2: Business Focus (4 questions)**

5. **What's your primary market area?** ✅ Required
   - Type: Text
   - Example: "Miami, FL"
   - Stores: As FACT (business_focus)

6. **What property types do you specialize in?** ✅ Required
   - Type: Multi-select
   - Options: Residential, Commercial, Land, Multi-family, Luxury, Investment, Condos, Single-family
   - Stores: As FACT (business_focus)

7. **What's your typical minimum property price?** ✅ Required
   - Type: Choice
   - Options: Under $200k, $200k-$400k, $400k-$600k, $600k-$1M, $1M+
   - Stores: As FACT (price range)

8. **What's your typical maximum property price?** ✅ Required
   - Type: Choice
   - Options: Under $200k, $200k-$400k, $400k-$600k, $600k-$1M, $1M+
   - Stores: As FACT (price range)

9. **How many deals do you typically close per month?** ✅ Required
   - Type: Choice
   - Options: 1-2 deals, 3-5 deals, 5-10 deals, 10+ deals
   - Stores: As FACT (business_metrics)

---

### **Category 3: Target Clients (2 questions)**

10. **Who are your primary clients?** ✅ Required
    - Type: Multi-select
    - Options: First-time buyers, Investors, Luxury buyers, Sellers, Relocation, Vacation homes, Rentals
    - Stores: As PREFERENCE (per client type)

11. **What are your main lead sources?** ✅ Required
    - Type: Multi-select
    - Options: Zillow, Realtor.com, Referrals, Social media, Website, Cold calling, Open houses, Networking
    - Stores: As FACT (business_strategy)

---

### **Category 4: Technology (3 questions)**

12. **Do you currently use a CRM system?** ✅ Required
    - Type: Choice
    - Options: Yes, No, Looking for one

13. **Which CRM do you use?**
    - Type: Text
    - Example: "Follow Up Boss, KVCore"
    - Stores: As FACT (technology)

14. **How comfortable are you with technology?** ✅ Required
    - Type: Choice
    - Options: Very comfortable, Somewhat comfortable, Learning, Prefer traditional methods
    - Stores: As FACT (communication)

---

### **Category 5: Goals (3 questions)**

15. **What's your monthly revenue goal?** ✅ Required
    - Type: Choice
    - Options: Under $10k, $10k-$25k, $25k-$50k, $50k-$100k, $100k+
    - Stores: As GOAL (priority: high)

16. **What's your biggest business challenge?** ✅ Required
    - Type: Choice
    - Options: Finding qualified leads, Following up consistently, Closing deals, Managing time, Staying organized, Marketing
    - Stores: As OBSERVATION (business_challenge)

17. **What do you want AI help with most?** ✅ Required
    - Type: Multi-select
    - Options:
      - Lead follow-up automation
      - Property research & analysis
      - Contract management
      - Market insights
      - Daily planning
      - Client communication
      - Task reminders
      - Deal negotiation
    - Stores: As PREFERENCE (per help area)

---

### **Category 6: Communication (3 questions)**

18. **What are your preferred working hours?** ✅ Required
    - Type: Choice
    - Options: Early bird (6AM-2PM), Standard (9AM-5PM), Flexible, Night owl (12PM-8PM)
    - Stores: As PREFERENCE (working hours)

19. **How do you prefer to receive updates?** ✅ Required
    - Type: Multi-select
    - Options: Email digest, SMS alerts, Push notifications, Daily briefing, Weekly summary
    - Stores: As FACT (communication)

20. **Would you like a weekly performance summary?** ✅ Required
    - Type: Boolean
    - Stores: As PREFERENCE (weekly checkin)

---

## 🚀 API Usage

### **Get All Onboarding Questions**

```bash
GET /onboarding/questions
```

**Response:**
```json
{
  "question_id": "agent_name",
  "question": "What's your full name?",
  "type": "text",
  "placeholder": "John Smith",
  "required": true,
  "category": "basic"
}
```

---

### **Get Questions by Category**

```bash
GET /onboarding/questions?category=business
```

**Categories:** `basic`, `business`, `clients`, `technology`, `goals`, `communication`

---

### **Submit Onboarding Answers**

```bash
POST /onboarding/submit

{
  "agent_id": 2,
  "session_id": "agent-session-456",
  "answers": {
    "agent_name": "Sarah Johnson",
    "agent_email": "sarah@miamirealty.com",
    "brokerage_name": "Miami Realty Partners",
    "primary_market": "Miami, FL",
    "property_types": ["Condos", "Luxury"],
    "price_range_min": "$600k-$1M",
    "price_range_max": "$1M+",
    "deal_volume": "5-10 deals",
    "target_clients": ["Luxury buyers", "Investors"],
    "monthly_goals": "$50k-$100k",
    "biggest_challenge": "Managing time",
    "want_help_with": ["Daily planning", "Task reminders", "Lead follow-up"]
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Onboarding answers saved successfully",
  "agent_id": 2,
  "answers_saved": 18
}
```

---

### **Generate Personalized Welcome**

```bash
POST /onboarding/welcome

{
  "agent_id": 2,
  "session_id": "agent-session-456"
}
```

**Response:**
```json
{
  "status": "success",
  "welcome_message": "Welcome to AI Realtor, Sarah! I'm excited to help you grow your business at Miami Realty Partners...",
  "agent_name": "Sarah Johnson",
  "onboarding_complete": true
}
```

**Example Welcome Message:**
```
Welcome to AI Realtor, Sarah!

I'm excited to help you grow your business at Miami Realty Partners.
I see you're an experienced agent focusing on luxury condos and
investment properties in the Miami market, typically closing 5-10
deals per month in the $600k-$1M+ range.

I know managing time is your biggest challenge, so I'll focus on:
• Daily planning and task prioritization
• Automated follow-up reminders
• Lead nurturing to save you time

Your goal of $50k-$100k monthly revenue is ambitious but achievable!
I'll help you stay organized and on track with weekly performance
summaries and daily briefings.

Let's get started! What would you like to work on first?
```

---

## 💾 How Answers Are Stored in Memory

### **Identity Memory**
```python
{
  "node_type": "identity",
  "summary": "Sarah Johnson - Miami Realty Partners",
  "importance": 0.92,
  "payload": {
    "name": "Sarah Johnson",
    "email": "sarah@miamirealty.com",
    "brokerage": "Miami Realty Partners",
    "experience": "5-10 years"
  }
}
```

### **Business Facts**
```python
{
  "node_type": "fact",
  "summary": "Primary market: Miami, FL",
  "category": "business_focus",
  "importance": 0.75
}

{
  "node_type": "fact",
  "summary": "Specializes in: Condos, Luxury",
  "category": "business_focus",
  "importance": 0.75
}

{
  "node_type": "fact",
  "summary": "Typical price range: $600k-$1M - $1M+",
  "category": "business_focus",
  "importance": 0.75
}
```

### **Client Preferences**
```python
{
  "node_type": "preference",
  "summary": "Targets luxury buyers",
  "importance": 0.85,
  "linked_to": "agent_2"
}

{
  "node_type": "preference",
  "summary": "Targets investors",
  "importance": 0.85,
  "linked_to": "agent_2"
}
```

### **Goals**
```python
{
  "node_type": "goal",
  "summary": "Achieve $50k-$100k in monthly revenue",
  "priority": "high",
  "importance": 0.95
}
```

### **Observations**
```python
{
  "node_type": "observation",
  "summary": "Biggest challenge: Managing time",
  "category": "business_challenge",
  "confidence": 1.0,
  "importance": 0.82
}
```

### **AI Help Preferences**
```python
{
  "node_type": "preference",
  "summary": "Wants AI help with daily planning",
  "importance": 0.85
}

{
  "node_type": "preference",
  "summary": "Wants AI help with task reminders",
  "importance": 0.85
}
```

---

## 🎯 After Onboarding: Personalized Experience

Once onboarding is complete, the AI provides **tailored assistance**:

### **Daily Briefing Example**
```
Good morning, Sarah! Here's your daily briefing:

📊 PORTFOLIO: 12 luxury condos, 8 investment properties
⚠️ URGENT: 3 luxury buyers need follow-up (priority: high)
📞 FOLLOW-UPS: 5 leads to call (focus on your luxury buyers)
🎯 GOAL TRACKING: $42k revenue this month (on track for $50k+)

AI FOCUS AREAS (your preferences):
• Task prioritization (biggest challenge: managing time)
• Daily planning (start with your top 3 priorities)
• Automated follow-ups (luxury buyers need attention)

MARKET INSIGHTS (Miami condos $600k-$1M+):
• 7 new listings this week (2 luxury, 5 investment)
• Average DOM: 45 days (up from 38 last month)
• Price trend: Stable (+2% vs last quarter)

What would you like to focus on?
```

### **Smart Task Recommendations**
```
Based on your goals and preferences, I recommend:

1. 📞 Call 3 luxury buyers (high priority)
   - They're pre-approved for $1M+
   - 2 have been waiting 3+ days

2. 📝 Review 2 new luxury condo listings
   - Just listed yesterday in Miami Beach
   - Match your investor criteria

3. 📊 Check on 2 pending contracts
   - Both close this week
   - Might need your attention

Should I prioritize these for you?
```

---

## 📊 Onboarding Progress Tracking

### **Check Onboarding Status**

```bash
GET /onboarding/status/{agent_id}?session_id=agent-session-456
```

**Response:**
```json
{
  "agent_id": 2,
  "onboarding_complete": true,
  "onboarding_progress": 100,
  "identity_exists": true,
  "total_memories": 18
}
```

**Progress calculation:**
- 5+ memories = 25% progress
- 10+ memories = 50% progress
- 15+ memories = 75% progress
- 18+ memories = 100% complete

---

## 🎨 Frontend Integration

### **Step 1: Fetch Questions**
```typescript
const response = await fetch('/onboarding/questions');
const questions = await response.json();

// Display in multi-step form
```

### **Step 2: Submit Answers**
```typescript
const answers = {
  agent_name: "Sarah Johnson",
  agent_email: "sarah@example.com",
  // ... all 18 answers
};

await fetch('/onboarding/submit', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    agent_id: 2,
    session_id: 'agent-session-456',
    answers
  })
});
```

### **Step 3: Get Welcome Message**
```typescript
const response = await fetch('/onboarding/welcome', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    agent_id: 2,
    session_id: 'agent-session-456'
  })
});

const { welcome_message } = await response.json();

// Display welcome message
```

---

## 🔧 Customization

### **Adding New Questions**

Edit `app/services/onboarding_service.py`:

```python
OnboardingQuestion(
    question_id="new_question",
    question="Your new question here?",
    question_type="choice",
    options=["Option 1", "Option 2", "Option 3"],
    required=True,
    category="custom"
)
```

### **Question Types**

- `text` — Free-form text input
- `choice` — Single select from options
- `multiselect` — Multiple select from options
- `boolean` — Yes/No
- `number` — Numeric input

---

## 📈 Benefits of Onboarding

### **For Agents:**
✅ **Personalized experience** from day one
✅ **AI understands their business** immediately
✅ **Relevant recommendations** based on their focus
✅ **Goals tracked automatically**
✅ **Preferences remembered forever**

### **For the AI:**
✅ **Context from first message** — no learning curve
✅ **Knows agent's priorities** — can prioritize tasks
✅ **Understands agent's challenges** — can help where needed most
✅ **Aware of agent's goals** — can track progress
✅ **Tailored communication style** — based on tech comfort

---

## 🎉 Summary

The onboarding system captures:

- ✅ **18 questions** across 6 categories
- ✅ **Basic info** — Name, email, brokerage
- ✅ **Business focus** — Market, property types, price range
- ✅ **Target clients** — Who they serve
- ✅ **Technology** — Current tools and tech comfort
- ✅ **Goals** — Revenue targets and challenges
- ✅ **Communication** — Preferred hours and methods

All stored in the **Memory Graph** for:
- Instant personalization
- Context-aware assistance
- Goal tracking
- Tailored recommendations

**Agents feel understood from day one! 🎯**

---

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)
