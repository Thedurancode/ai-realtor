# Contract Auto-Attach - Quick Reference

## ✅ Implementation Complete!

Your AI Realtor platform now **automatically attaches required contracts** to properties based on state, property type, and other criteria!

---

## 🎯 What It Does

When you create a property, the system:
1. ✅ Identifies applicable contract templates for that state/city
2. ✅ Filters by property type, price range
3. ✅ Auto-attaches contracts marked with `auto_attach_on_create = true`
4. ✅ Creates contracts in DRAFT status
5. ✅ Returns voice confirmation with count of attached contracts

---

## 📁 Files Created

- `app/models/contract_template.py` - Contract template model
- `app/schemas/contract_template.py` - Pydantic schemas
- `app/services/contract_auto_attach.py` - Auto-attach logic
- `app/routers/contract_templates.py` - Template management API (12 endpoints)
- `seed_contract_templates.py` - 15 pre-configured templates

**Modified:**
- `app/routers/properties.py` - Auto-attach on create
- `app/routers/contracts.py` - Added 4 new endpoints for contract status
- `app/routers/__init__.py` - Exported contract_templates_router
- `app/main.py` - Included contract_templates_router

---

## 🚀 Quick Start

### 1. Deploy
```bash
fly deploy
```

### 2. Seed Templates
```bash
python3 seed_contract_templates.py
```

### 3. Link DocuSeal Templates
```bash
# Create templates in DocuSeal dashboard
# Then update each template with DocuSeal ID:
curl -X PATCH "https://ai-realtor.fly.dev/contract-templates/1" \
  -H "Content-Type: application/json" \
  -d '{"docuseal_template_id": "your_docuseal_id"}'
```

### 4. Test
```bash
# Create a NY property
curl -X POST "https://ai-realtor.fly.dev/properties/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Property",
    "address": "123 Main St",
    "city": "New York",
    "state": "NY",
    "price": 500000,
    "property_type": "house",
    "agent_id": 1
  }'

# Check contracts - should see 3 auto-attached!
curl "https://ai-realtor.fly.dev/contracts/property/1"
```

---

## 📚 Key Endpoints

### Template Management
```bash
# Create template
POST /contract-templates/

# List templates
GET /contract-templates/?state=NY

# Update template
PATCH /contract-templates/{id}
```

### Contract Status
```bash
# Manually attach contracts
POST /contracts/property/{property_id}/auto-attach

# Check if ready to close
GET /contracts/property/{property_id}/required-status

# Get missing contracts
GET /contracts/property/{property_id}/missing-contracts

# Voice status check
POST /contracts/voice/check-contracts?address_query=141+throop
```

---

## 🎙️ Voice Commands

Your voice agent can now say:

✅ **On property creation:**
"I've created a new listing for 123 Main Street. Listed at $500,000. I've also attached 3 required contracts that need to be signed."

✅ **When checking status:**
"Contract status for 141 Throop Ave: 2 contracts completed, 1 in progress. The property is not ready to close yet."

✅ **When checking readiness:**
"Great news! 141 Throop has all 3 required contracts completed. The property is ready to close."

---

## 📊 Pre-Configured Templates

The system comes with **15 contract templates**:

**New York (3)**
- Property Condition Disclosure Statement (REQUIRED)
- Lead-Based Paint Disclosure (REQUIRED)
- Purchase and Sale Agreement (REQUIRED)

**California (3)**
- Transfer Disclosure Statement (REQUIRED)
- Natural Hazard Disclosure (REQUIRED)
- Residential Purchase Agreement (REQUIRED)

**Florida (3)**
- Seller's Property Disclosure (RECOMMENDED)
- HOA Disclosure (REQUIRED)
- Residential Purchase Agreement (REQUIRED)

**Texas (2)**
- Seller's Disclosure Notice (REQUIRED)
- Residential Purchase Contract (REQUIRED)

**Universal (4)**
- Home Inspection Contingency (RECOMMENDED)
- Financing Contingency (RECOMMENDED)
- Federal Lead-Based Paint Disclosure (REQUIRED for pre-1978)

---

## 🔄 Typical Workflow

1. **Create Property** → 3 contracts auto-attach (DRAFT)
2. **Check Status** → See what's attached
3. **Send Contracts** → DocuSeal sends to recipients
4. **Monitor Progress** → Track who signed
5. **Verify Complete** → Check `is_ready_to_close`
6. **Close Deal** → All required contracts done!

---

## 💡 Example Use Cases

### Use Case 1: New Property
```
User: "Create a listing for 555 Park Avenue, NY"
System: Auto-attaches 3 NY contracts
Agent: "Property created with 3 required contracts attached"
```

### Use Case 2: Check Readiness
```
User: "Is 141 throop ready to close?"
System: Checks required contract status
Agent: "Not yet. 1 contract is in progress and 1 is missing"
```

### Use Case 3: Existing Property
```
User: "Attach missing contracts to property 5"
System: Scans templates, attaches what's missing
Result: 2 contracts added
```

---

## 🎊 What You Now Have

✅ **Automatic Contract Attachment**
- Properties auto-get contracts on creation
- Voice confirmation mentions count

✅ **Smart Filtering**
- By state, city, property type, price
- Configurable priority

✅ **Status Tracking**
- Check what's completed
- Check what's missing
- Check if ready to close

✅ **Voice Integration**
- Natural language status checks
- Voice-friendly responses

✅ **Template Management**
- Full CRUD API
- Activate/deactivate templates
- Easy DocuSeal integration

✅ **15 Pre-Configured Templates**
- NY, CA, FL, TX + Universal
- Ready to use after linking DocuSeal

---

## 📖 Full Documentation

See `CONTRACT_AUTO_ATTACH_GUIDE.md` for:
- Complete API reference
- All endpoint examples
- Database schema
- Integration guide
- Voice command examples

---

## 🎯 Next Steps

1. ✅ Deploy application
2. ✅ Seed contract templates
3. ✅ Create DocuSeal templates
4. ✅ Link DocuSeal template IDs
5. ✅ Test with new property
6. ✅ Integrate with voice agent

**Your contract auto-attach system is ready!** 🚀
