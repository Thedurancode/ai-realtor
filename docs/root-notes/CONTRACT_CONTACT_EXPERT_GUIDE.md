# 🤖 Contract & Contact Expert - Complete Guide

## Overview

Your AI Realtor bot is now an **expert in contract management and contact identification**. It will proactively monitor contracts, identify missing contacts, and recommend actions.

---

## ✨ New Capabilities

### 1. Automatic Contract Status Checking

The bot will **automatically check contract status** when:
- ✅ You mention a property
- ✅ Property changes to "waiting_for_contracts" status
- ✅ You ask about "readiness" or "what's next"
- ✅ You mention closing, offers, or deals
- ✅ You ask "what contracts are needed?"

### 2. Proactive Contact Identification

The bot will **automatically identify when contacts are needed** for:
- ✅ Sellers (from skip trace data)
- ✅ Buyers (when offers exist)
- ✅ Contract signers (based on required roles)
- ✅ Service providers (lenders, title companies, inspectors)

### 3. Smart Recommendations

The bot provides **actionable recommendations**:
- What contracts to attach
- What contacts to create
- What deadlines are approaching
- What's blocking the deal
- What to do next

---

## 💬 Voice Commands

### Check Contract Status
```
"Check contract status for property 1"
"What contracts does property 1 have?"
"Are all contracts signed for 123 Main St?"
"Show me contract status"
```

### Check Contact Status
```
"What contacts do we have for property 1?"
"Who are the parties involved in property 1?"
"Are we missing any contacts?"
"Show me all contacts for 123 Main St"
```

### Readiness Assessment
```
"Is property 1 ready to close?"
"What's needed to close property 1?"
"Check readiness for 123 Main St"
"What's blocking the deal?"
```

### Contract Actions
```
"Attach required contracts to property 1"
"Send the purchase agreement for signing"
"Check if contracts are overdue"
"What contracts are missing?"
```

### Contact Actions
```
"Create seller contact from skip trace"
"Add buyer contact: John Smith"
"I need a lender for property 1"
"Create contact for title company"
```

---

## 📊 Contract Status Meanings

| Status | Meaning | Action Needed |
|--------|---------|---------------|
| **DRAFT** | Created but not sent | Send to signers |
| **SENT** | Sent, awaiting response | Follow up in 2-3 days |
| **IN_PROGRESS** | Being signed | Monitor progress |
| **PENDING_SIGNATURE** | Waiting for signatures | Follow up urgently |
| **COMPLETED** | Fully signed | ✅ Done! |
| **CANCELLED** | Cancelled | May need replacement |
| **EXPIRED** | Expired | Re-send or extend |
| **ARCHIVED** | Archived | No action needed |

---

## 👥 Contact Roles

### Essential Contacts (Always Need)
- **seller** - Property owner
- **buyer** - Property purchaser

### Legal & Compliance
- **lawyer** / **attorney** - Legal representation
- **title_company** - Title/closing services

### Financing
- **lender** - Mortgage lender
- **mortgage_broker** - Mortgage broker

### Property Services
- **inspector** - Home inspector
- **appraiser** - Property appraiser
- **contractor** - Repairs/renovations
- **stager** - Home staging
- **photographer** - Property photos

### Other Stakeholders
- **property_manager** - Property management
- **tenant** - Current tenant
- **landlord** - Property landlord
- **handyman**, **plumber**, **electrician** - Tradespeople

---

## 🔄 Automated Workflows

### When Property is Created
```
1. Property created
   ↓
2. Bot monitors status
   ↓
3. When enriched → Suggest skip trace
   ↓
4. When skip traced → Create seller contact
   ↓
5. When researched → Attach contracts
   ↓
6. Alert if contacts needed for signing
```

### When Contracts are Attached
```
1. Contracts attached to property
   ↓
2. Bot checks required_signer_roles for each contract
   ↓
3. Identifies missing contacts
   ↓
4. Creates alert with recommendations
   ↓
5. Offers to create contacts
```

### When Checking Readiness
```
1. User asks "Is it ready to close?"
   ↓
2. Bot checks all required contracts
   ↓
3. Bot checks all signer contacts exist
   ↓
4. Bot checks contract statuses
   ↓
5. Provides comprehensive status report
   ↓
6. Recommends next actions
```

---

## 📱 Example Bot Responses

### Contract Status Check

**User:** "What's the contract status for property 1?"

**Bot:**
```
📄 **Contract Status - Property #1 (123 Main St)**

Progress: ████████░░ 80% complete

✅ **Completed (4 contracts):**
  1. Purchase Agreement - All signed ✓
  2. Seller Disclosure - Complete ✓
  3. Lead-Based Paint - Signed ✓
  4. Property Inspection - Reviewed ✓

⏳ **Pending (1 contract):**
  1. Mortgage Contingency - Awaiting buyer signature
     ⚠️ Due: Tomorrow 5 PM
     📞 Action needed: Follow up with buyer

**Recommendation:** Contact buyer John Smith about mortgage
contingency signature urgently (due tomorrow).
```

---

### Missing Contacts Alert

**User:** "What contacts do we need for property 2?"

**Bot:**
```
👥 **Contact Status - Property #2 (141 Throop Ave)**

❌ **Critical Contacts Missing:**

1. **Seller** - REQUIRED
   🔍 Source: Skip trace completed
   💡 Action: Create from skip trace data

2. **Buyer** - REQUIRED
   🤷 No buyer information yet
   💡 Action: Get buyer details

⚠️ **Optional Contacts:**
• Lender - If financing needed
• Title Company - For closing
• Inspector - For inspection

**Quick Actions:**
• Create seller from skip trace
• Add buyer contact
• Set up inspection

Want me to create these contacts now?
```

---

### Ready to Close Assessment

**User:** "Is property 1 ready to close?"

**Bot:**
```
🎉 **YES! Ready to Close!**

Property #1 (123 Main St) has everything needed:

✅ **Contracts:** All 5 required contracts signed
✅ **Contacts:** All parties identified
✅ **Skip Trace:** Seller information complete
✅ **Enrichment:** Zillow data gathered

**Next Steps:**
1. 📅 Schedule closing date
2. 🏢 Coordinate with title company
3. 🚪 Final walkthrough
4. 🎊 Celebrate!

Would you like me to help with any of these?
```

---

### Blocking Issues

**User:** "What's blocking property 2?"

**Bot:**
```
⚠️ **Deal Blockers Identified - Property #2**

🚨 **Critical Blockers:**

1. **No Contracts Attached**
   Status: Waiting for contracts
   Impact: Cannot proceed to closing
   ✅ Solution: Attach required contracts now

2. **Missing Seller Contact**
   Cannot sign contracts without seller
   Impact: Cannot send contracts
   ✅ Solution: Skip trace to find seller

3. **No Buyer Identified**
   Don't know who's purchasing
   Impact: Cannot prepare purchase agreement
   ✅ Solution: Get buyer information

**Recommended Actions:**
1. Run skip trace to find seller
2. Attach required contracts
3. Identify buyer

Want me to skip trace property 2 now?
```

---

## 🔔 Proactive Alerts

The bot will **automatically alert you** when:

### Overdue Deadlines
```
⚠️ **URGENT: Contract Deadline Today!**

Property #1 - Mortgage Contingency
Due: Today at 5 PM
Status: Awaiting signature

Action: Follow up with buyer immediately!
```

### Stuck Contracts
```
⏳ **Contract Stuck for 5 Days**

Property #2 - Purchase Agreement
Status: DRAFT (not sent)
Created: 5 days ago

Action: Send contract to signers now
```

### Missing Critical Contacts
```
👤 **Contact Needed: Seller**

Property #3 needs seller contact to sign contracts

Skip trace found: Jane Doe
Phone: Available in skip trace

Action: Create seller contact now?
```

### Ready to Close
```
🎉 **Congratulations! Property Ready to Close!**

Property #1 has all contracts signed
All contacts identified
Ready for closing!

Next: Schedule closing date
```

---

## 🎯 Best Practices

### For the User

1. **Always Ask About Status**
   - "What's the status of property X?"
   - Bot will check contracts and contacts automatically

2. **Trust Bot Recommendations**
   - Bot identifies missing contacts before contracts
   - Bot catches overdue deadlines
   - Bot suggests next actions

3. **Use Bot's Expertise**
   - Ask "What contracts do I need?"
   - Ask "Who are we missing?"
   - Ask "What's blocking the deal?"

### Contract Workflow

```
1. Create Property
   ↓
2. Enrich with Zillow
   ↓
3. Skip Trace (find seller)
   ↓
4. Create Seller Contact
   ↓
5. Attach Contracts
   ↓
6. Identify Missing Signers
   ↓
7. Create All Signer Contacts
   ↓
8. Send Contracts for Signing
   ↓
9. Monitor Progress
   ↓
10. Close Deal! 🎉
```

---

## 📊 Quick Reference Commands

### Contract Management
```bash
# Check status
curl "$AI_REALTOR_API_URL/properties/1"

# Get contracts
curl "$AI_REALTOR_API_URL/contracts/?property_id=1"

# Check readiness
curl "$AI_REALTOR_API_URL/properties/1/contract-readiness"

# Attach contracts
curl -X POST "$AI_REALTOR_API_URL/properties/1/attach-contracts"

# Send for signing
curl -X POST "$AI_REALTOR_API_URL/contracts/3/send" \
  -d '{"signer_roles": ["buyer", "seller"]}'
```

### Contact Management
```bash
# List contacts
curl "$AI_REALTOR_API_URL/contacts/?property_id=1"

# Add contact
curl -X POST "$AI_REALTOR_API_URL/contacts/" \
  -d '{"property_id": 1, "name": "John", "role": "buyer"}'

# Get skip trace info
curl "$AI_REALTOR_API_URL/properties/1" | jq '.skip_traces'
```

---

## 🎓 What the Bot Knows

The bot is now an expert on:

✅ **Contract Types**
   - Purchase agreements
   - Seller disclosures
   - Lead-based paint
   - Property inspections
   - Mortgage contingencies
   - And 15+ more types

✅ **Contract Statuses**
   - What each status means
   - What action is needed
   - When to follow up
   - When contracts are overdue

✅ **Contact Roles**
   - When each contact is needed
   - How to match signers to contracts
   - What roles are essential vs optional
   - How to create contacts from skip trace

✅ **Deadlines**
   - What's due when
   - What's overdue
   - What's urgent
   - What can wait

✅ **Workflow**
   - What order to do things
   - What's blocking progress
   - What's ready to close
   - What to do next

---

## 🚀 Try It Now!

Open Telegram (@Smartrealtoraibot) and try:

### Check Status
```
"What's the contract status for property 1?"
"Are we ready to close property 1?"
"What's blocking property 2?"
```

### Get Recommendations
```
"What contracts do I need for property 2?"
"What contacts are we missing?"
"What should I do next with property 1?"
```

### Take Action
```
"Attach required contracts to property 1"
"Create seller contact from skip trace"
"Check if any contracts are overdue"
```

The bot will provide expert guidance with clear, actionable recommendations! 🎯
