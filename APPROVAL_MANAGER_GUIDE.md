# 🔐 Approval Manager — Complete Guide

## Overview

The Approval Manager provides **interactive supervision** for high-risk operations in the AI Realtor platform. Inspired by ZeroClaw's approval system, it adds a security layer that requires explicit approval for dangerous operations while maintaining efficiency with auto-approve rules and session allowlists.

---

## 🎯 What It Does

The Approval Manager:

✅ **Classifies operations by risk level** — critical, high, medium, low
✅ **Requires approval for dangerous operations** — delete, send contracts, withdraw offers
✅ **Auto-approves read-only operations** — get_property, list_properties, analytics
✅ **Maintains session allowlists** — approve once, auto-approve next time
✅ **Logs all approval decisions** — comprehensive audit trail
✅ **Supports three autonomy levels** — supervised, semi_auto, full_auto
✅ **Scrubs sensitive data** — automatic redaction from audit logs

---

## 🚨 Risk Categories

### **Critical Risk** (Always requires approval)
- `delete_property` — Delete a property and all related data
- `delete_contact` — Delete a contact
- `delete_contract` — Delete a contract
- `cancel_all_campaigns` — Cancel all voice campaigns
- `clear_conversation_history` — Clear conversation history

### **High Risk** (Requires approval in supervised/semi-auto)
- `send_contract` — Send contract for signature
- `withdraw_offer` — Withdraw an offer
- `skip_trace_property` — Skip trace to find owner (costs money)
- `bulk_operation` — Execute operation across multiple properties

### **Medium Risk** (Requires approval in supervised mode)
- `update_property` — Update property details
- `create_property` — Create new property
- `add_contact` — Add contact
- `attach_required_contracts` — Attach contract templates
- `execute_workflow` — Execute workflow template
- `create_voice_campaign` — Create voice campaign
- `create_offer` — Create offer
- `accept_offer` — Accept offer
- `reject_offer` — Reject offer
- `counter_offer` — Counter offer

### **Low Risk** (Auto-approved)
- `get_property` — Get property details
- `list_properties` — List properties
- `get_property_recap` — Get property recap
- `enrich_property` — Enrich with Zillow data
- `generate_property_recap` — Generate AI recap
- `make_property_phone_call` — Make phone call
- `create_scheduled_task` — Create reminder/task
- All read-only analytics and dashboard operations

---

## 🎛️ Autonomy Levels

### **Supervised Mode** (Default — Safest)
```
✅ Auto-approves: Read-only operations (get, list, analytics)
⚠️  Requires approval: Everything else (create, update, delete, send, execute)
❌ Blocks: Nothing (all operations can be approved)
```

**Use case:** New agents, testing, high-value transactions

---

### **Semi-Auto Mode** (Balanced)
```
✅ Auto-approves: Read-only + low/medium risk operations
⚠️  Requires approval: Critical + high risk operations
❌ Blocks: Critical operations unless explicitly approved
```

**Use case:** Experienced agents, production use

---

### **Full Auto Mode** (Fastest — Least Safe)
```
✅ Auto-approves: ALL operations
⚠️  Requires approval: Nothing
❌ Blocks: Nothing
```

**Use case:** Fully autonomous agents, high-trust environments

---

## 📡 API Usage

### **1. Check if Approval Required**

```bash
POST /approval/request

{
  "session_id": "agent-session-123",
  "tool_name": "send_contract",
  "input_data": {
    "property_id": 5,
    "contract_id": 3
  }
}
```

**Response (Approved):**
```json
{
  "granted": true,
  "reason": "Auto-approved (read-only or previously approved)",
  "autonomy_level": "supervised",
  "timestamp": "2026-02-22T10:30:00Z"
}
```

**Response (Denied):**
```json
{
  "granted": false,
  "reason": "Manual approval required for high-risk operation: send_contract. Use the approval API to grant permission.",
  "autonomy_level": "supervised",
  "timestamp": "2026-02-22T10:30:00Z"
}
```

---

### **2. Grant Approval**

```bash
POST /approval/grant

{
  "session_id": "agent-session-123",
  "tool_name": "send_contract",
  "add_to_allowlist": true
}
```

**Response:**
```json
{
  "status": "approved",
  "tool_name": "send_contract",
  "session_id": "agent-session-123",
  "added_to_allowlist": true,
  "allowlist_size": 5
}
```

**Now future calls to `send_contract` in this session are auto-approved!**

---

### **3. Deny Approval**

```bash
POST /approval/deny

{
  "session_id": "agent-session-123",
  "tool_name": "delete_property",
  "reason": "Cannot delete property with active contracts"
}
```

**Response:**
```json
{
  "status": "denied",
  "tool_name": "delete_property",
  "session_id": "agent-session-123",
  "reason": "Cannot delete property with active contracts"
}
```

---

### **4. Get Audit Log**

```bash
GET /approval/audit-log?session_id=agent-session-123&limit=50
```

**Response:**
```json
{
  "total_entries": 25,
  "entries": [
    {
      "session_id": "agent-session-123",
      "tool_name": "send_contract",
      "granted": true,
      "risk_level": "high",
      "timestamp": "2026-02-22T10:30:00Z",
      "reason": "Approved by agent",
      "input_summary": "{\"property_id\": 5, \"contract_id\": 3}",
      "autonomy_level": "supervised"
    },
    {
      "session_id": "agent-session-123",
      "tool_name": "delete_property",
      "granted": false,
      "risk_level": "critical",
      "timestamp": "2026-02-22T10:25:00Z",
      "reason": "Critical-risk operations require explicit approval",
      "input_summary": "{\"property_id\": 12}",
      "autonomy_level": "supervised"
    }
  ]
}
```

---

### **5. Get Session Allowlist**

```bash
GET /approval/allowlist/agent-session-123
```

**Response:**
```json
{
  "session_id": "agent-session-123",
  "approved_tools": [
    "send_contract",
    "create_offer",
    "update_property",
    "add_contact",
    "attach_required_contracts"
  ],
  "total": 5
}
```

---

### **6. Clear Session Allowlist**

```bash
DELETE /approval/allowlist/agent-session-123
```

**Response:**
```json
{
  "status": "cleared",
  "session_id": "agent-session-123"
}
```

**Use this when agent logs out or session ends.**

---

### **7. Change Autonomy Level**

```bash
PUT /approval/autonomy-level

{
  "level": "semi_auto"
}
```

**Response:**
```json
{
  "status": "updated",
  "level": "semi_auto"
}
```

**Levels:** `supervised`, `semi_auto`, `full_auto`

---

### **8. Get Current Autonomy Level**

```bash
GET /approval/autonomy-level
```

**Response:**
```json
{
  "level": "supervised",
  "description": "All operations require approval except read-only"
}
```

---

### **9. Get Risk Categories**

```bash
GET /approval/risk-categories
```

**Response:**
```json
{
  "critical": [
    "delete_property",
    "delete_contact",
    "delete_contract",
    "cancel_all_campaigns",
    "clear_conversation_history"
  ],
  "high": [
    "send_contract",
    "withdraw_offer",
    "skip_trace_property",
    "bulk_operation"
  ],
  "medium": [
    "update_property",
    "create_property",
    "add_contact",
    "attach_required_contracts",
    "execute_workflow",
    "create_voice_campaign",
    "create_offer",
    "accept_offer",
    "reject_offer",
    "counter_offer"
  ],
  "low": [
    "get_property",
    "list_properties",
    "get_property_recap",
    "enrich_property",
    "generate_property_recap",
    "make_property_phone_call",
    "create_scheduled_task"
  ]
}
```

---

### **10. Get Approval Configuration**

```bash
GET /approval/config
```

**Response:**
```json
{
  "autonomy_level": "supervised",
  "auto_approve_count": 58,
  "always_ask_count": 10,
  "max_session_allowlist_size": 50,
  "active_sessions": 3
}
```

---

## 🔒 Security Features

### **Credential Scrubbing**

All input data is automatically scrubbed before logging:

```python
# Input:
{
  "api_key": "sk-ant-1234567890",
  "email": "agent@example.com",
  "property_id": 5
}

# Logged as:
{
  "api_key": "***REDACTED***",
  "email": "agent@example.com",
  "property_id": 5
}
```

**Sensitive fields detected:**
- `password`, `token`, `api_key`, `secret`, `key`
- `ssn`, `social_security`, `credit_card`, `account_number`

---

### **Audit Logging**

All approval decisions are logged with:
- Session ID
- Tool name
- Granted/denied status
- Risk level
- Timestamp
- Reason
- Input summary (scrubbed)
- Autonomy level

**Log retention:** In-memory (can be extended to database)

---

### **Session Allowlist Limits**

Maximum allowlist size per session: **50 tools**

When limit is reached, oldest entry is removed (FIFO).

**Prevents allowlist bloat.**

---

## 💡 Integration with MCP Tools

### **Option 1: Check Before Execution**

```python
from app.services.approval import approval_manager

async def send_contract(property_id: int, contract_id: int, session_id: str):
    # Check if approval required
    if await approval_manager.requires_approval("send_contract", session_id):
        result = await approval_manager.request_approval(
            session_id=session_id,
            tool_name="send_contract",
            input_data={"property_id": property_id, "contract_id": contract_id}
        )

        if not result.granted:
            raise PermissionError(result.reason)

    # Proceed with operation
    # ... send contract logic
```

---

### **Option 2: Middleware Pattern**

```python
from functools import wraps
from app.services.approval import approval_manager

def require_approval(tool_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            session_id = kwargs.get("session_id")

            result = await approval_manager.request_approval(
                session_id=session_id,
                tool_name=tool_name,
                input_data=kwargs
            )

            if not result.granted:
                raise PermissionError(result.reason)

            return await func(*args, **kwargs)
        return wrapper
    return decorator

@require_approval("send_contract")
async def send_contract(property_id: int, contract_id: int, session_id: str):
    # ... send contract logic
```

---

## 🎯 Best Practices

### **1. Start in Supervised Mode**
```python
# New agent setup
approval_manager.set_autonomy_level("supervised")
```

**Safer for new agents.**

---

### **2. Use Session Allowlists**
```python
# Agent approves send_contract once
await approval_manager.grant_approval(
    session_id="agent-session-123",
    tool_name="send_contract",
    add_to_allowlist=True
)

# Future calls auto-approved
```

**Reduces repeated approvals.**

---

### **3. Clear Allowlists on Logout**
```python
# Agent logs out
approval_manager.clear_session_allowlist("agent-session-123")
```

**Prevents unauthorized access.**

---

### **4. Audit Regularly**
```python
# Check recent approvals
log = approval_manager.get_audit_log(session_id="agent-session-123", limit=100)

# Look for suspicious patterns
for entry in log:
    if entry.risk_level == "critical" and entry.granted:
        print(f"CRITICAL: {entry.tool_name} at {entry.timestamp}")
```

**Catch unauthorized operations.**

---

### **5. Adjust Autonomy Level Based on Experience**
```python
# New agent
approval_manager.set_autonomy_level("supervised")

# After 1 month
approval_manager.set_autonomy_level("semi_auto")

# After 6 months with good track record
approval_manager.set_autonomy_level("full_auto")
```

**Balance safety and efficiency.**

---

## 📊 Example Workflows

### **Workflow 1: New Agent Onboarding**

```
1. Agent signs up
2. System sets autonomy_level = "supervised"
3. Agent tries to send contract
4. Approval denied: "Manual approval required for high-risk operation"
5. Agent calls POST /approval/grant
6. System adds to session allowlist
7. Agent retries sending contract
8. Approved automatically (in allowlist)
9. Contract sent successfully
```

---

### **Workflow 2: High-Value Transaction**

```
1. Experienced agent (autonomy_level = "semi_auto")
2. Agent tries to delete property with active contracts
3. Approval denied: "Critical-risk operations require explicit approval"
4. Broker must call POST /approval/grant
5. System logs: "delete_property approved by broker"
6. Property deleted
7. Audit trail shows broker approval
```

---

### **Workflow 3: Autonomous Mode**

```
1. Trusted agent (autonomy_level = "full_auto")
2. Agent tries to send contract
3. Auto-approved immediately
4. Contract sent
5. Audit trail shows: "Auto-approved in full-autonomy mode"
6. No friction, full accountability
```

---

## 🔧 Configuration

### **Environment Variables** (Optional)

```bash
# .env
APPROVAL_AUTONOMY_LEVEL=supervised  # supervised, semi_auto, full_auto
APPROVAL_MAX_ALLOWLIST_SIZE=50
APPROVAL_AUDIT_LOG_RETENTION_DAYS=30
```

---

### **Code Configuration**

```python
from app.services.approval import ApprovalManager

# Custom approval manager
custom_approval = ApprovalManager(config={
    "level": "semi_auto",
    "auto_approve": ["get_property", "list_properties"],
    "always_ask": ["delete_property", "send_contract"],
    "max_session_allowlist_size": 100
})
```

---

## 🎭 Comparison with Command Filtering

| Feature | Command Filtering | Approval Manager |
|---------|-------------------|------------------|
| **Purpose** | Block dangerous commands | Interactive supervision |
| **Scope** | Command-level | Operation-level |
| **User Input** | No (requires `confirmed=true`) | Yes (grant/deny API) |
| **Audit Trail** | Basic | Comprehensive |
| **Session Memory** | No | Yes (allowlist) |
| **Autonomy Levels** | No | Yes (3 levels) |
| **Risk Classification** | No | Yes (4 levels) |

**Use both together for maximum security!**

---

## ✅ Summary

**The Approval Manager provides:**

✅ **Risk-based operation classification** — critical, high, medium, low
✅ **Interactive approval workflow** — grant/deny via API
✅ **Three autonomy levels** — supervised, semi_auto, full_auto
✅ **Session allowlists** — approve once, auto-approve next time
✅ **Comprehensive audit logging** — all decisions logged with scrubbed data
✅ **Credential scrubbing** — sensitive data auto-redacted
✅ **Flexible configuration** — customize for your use case

**Integrate with high-risk operations:**
- Send contracts
- Withdraw offers
- Skip trace (costs money)
- Delete operations
- Bulk operations
- Execute workflows

**Safer than command filtering alone, more flexible than manual approval!**

---

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)
