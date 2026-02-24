# 🔒 Credential Scrubbing — Complete Guide

## Overview

The Credential Scrubbing service automatically **redacts sensitive information** from tool outputs, logs, conversation history, and audit trails. Inspired by ZeroClaw's credential scrubbing, it prevents accidental exposure of secrets like API keys, passwords, tokens, SSNs, and credit cards.

---

## 🎯 What It Scrubs

### **API Keys**
- Anthropic Claude: `sk-ant-api123-4567890abcdef`
- OpenAI: `sk-1234567890abcdefghijklmno`
- AWS Access Key: `AKIA1234567890ABCDEFGHI`
- Google OAuth: `ya29.abc123xyz789`
- Generic: `api_key=...`, `key=...`, `secret=...`

### **Passwords**
- JSON format: `{"password": "mySecretPass123"}`
- Form format: `password=mySecretPass123`
- Short format: `pass=mySecretPass123`

### **Tokens**
- Bearer tokens: `Authorization: Bearer eyJhbGciOi...`
- JSON tokens: `{"token": "abc123xyz789"}`
- JWT tokens: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### **Personally Identifiable Information (PII)**
- SSNs: `123-45-6789`, `123 45 6789`, `123456789`
- Credit cards: `1234 5678 9012 3456`, `1234-5678-9012-3456`
- Email addresses: `user@example.com` (optional)
- Phone numbers: `+1-415-555-1234`, `(415) 555-1234` (optional)
- IP addresses: `192.168.1.1`, `10.0.0.1` (optional)

---

## 🚀 Quick Start

### **Basic Usage**

```python
from app.services.credential_scrubbing import scrub_credentials

# Scrub text
raw = "API key: sk-ant-api123-4567890abcdef"
clean = scrub_credentials(raw)
# Result: "API key: ***REDACTED***"

# Scrub JSON
data = {
    "api_key": "sk-ant-api123-4567890abcdef",
    "name": "My Service",
    "password": "secret123"
}
clean_data = scrub_credentials(data)
# Result: {
#   "api_key": "***REDACTED***",
#   "name": "My Service",
#   "password": "***REDACTED***"
# }
```

---

### **Keep Partial Values (for debugging)**

```python
# Keep 4 leading/trailing characters
clean = scrub_credentials(
    "API key: sk-ant-api123-4567890abcdef",
    config={"keep_chars": 4}
)
# Result: "API key: sk-a***cdef"
```

---

### **Disable Email/Phone/IP Scrubbing**

```python
clean = scrub_credentials(
    "Contact agent@example.com or call +1-415-555-1234",
    config={
        "scrub_email": False,
        "scrub_phone": False,
        "scrub_ip": False
    }
)
# Result: "Contact agent@example.com or call +1-415-555-1234"
```

---

## 📡 API Usage

### **1. Scrub Text**

```bash
POST /scrub/text

{
  "text": "API key: sk-ant-api123-4567890abcdef, password: secret123",
  "keep_chars": 0,
  "scrub_email": true,
  "scrub_phone": true,
  "scrub_ip": true
}
```

**Response:**
```json
{
  "original": "API key: sk-ant-api123-4567890abcdef, password: secret123",
  "scrubbed": "API key: ***REDACTED***, password: ***REDACTED***",
  "patterns_found": 2
}
```

---

### **2. Scrub JSON**

```bash
POST /scrub/json

{
  "data": {
    "api_key": "sk-ant-api123-4567890abcdef",
    "username": "john_doe",
    "password": "secret123",
    "contact": "agent@example.com"
  },
  "keep_chars": 0
}
```

**Response:**
```json
{
  "original": {
    "api_key": "sk-ant-api123-4567890abcdef",
    "username": "john_doe",
    "password": "secret123",
    "contact": "agent@example.com"
  },
  "scrubbed": {
    "api_key": "***REDACTED***",
    "username": "john_doe",
    "password": "***REDACTED***",
    "contact": "age***REDACTED***"
  },
  "patterns_found": 3
}
```

---

### **3. Test Scrubbing**

```bash
GET /scrub/test
```

**Response:**
```json
{
  "total_tests": 10,
  "passed": 10,
  "results": [
    {
      "name": "Anthropic API Key",
      "input": "API key: sk-ant-api123-4567890abcdef",
      "output": "API key: ***REDACTED***",
      "expected": "API key: ***REDACTED***",
      "passed": true
    },
    {
      "name": "Password (JSON)",
      "input": "{\"password\": \"mySecretPass123\"}",
      "output": "{\"password\": \"***REDACTED***\"}",
      "expected": "{\"password\": \"***REDACTED***\"}",
      "passed": true
    }
    // ... 8 more tests
  ]
}
```

---

### **4. Get Supported Patterns**

```bash
GET /scrub/patterns
```

**Response:**
```json
{
  "api_keys": [
    "Anthropic Claude: sk-ant-api123-...",
    "OpenAI: sk-...",
    "AWS Access Key: AKIA...",
    "Google OAuth: ya29....",
    "Generic: api_key=..., key=..., secret=..."
  ],
  "passwords": [
    "JSON: password\":\"...\"",
    "Form: password=...",
    "Short: pass=..."
  ],
  "tokens": [
    "Bearer token: Bearer ...",
    "JSON token: token\":\"...\"",
    "JWT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  ],
  "ssns": [
    "With dashes: 123-45-6789",
    "With spaces: 123 45 6789",
    "Plain: 123456789"
  ],
  "credit_cards": [
    "With spaces: 1234 5678 9012 3456",
    "With dashes: 1234-5678-9012-3456",
    "Plain: 1234567890123456"
  ],
  "emails": [
    "Standard: user@example.com",
    "Subdomain: user@mail.example.com"
  ],
  "phones": [
    "International: +1-415-555-1234",
    "With parentheses: (415) 555-1234",
    "Standard: 415-555-1234"
  ],
  "ip_addresses": [
    "IPv4: 192.168.1.1",
    "Private: 10.0.0.1"
  ]
}
```

---

### **5. Get Current Configuration**

```bash
GET /scrub/config
```

**Response:**
```json
{
  "redaction_string": "***REDACTED***",
  "keep_chars": 0,
  "scrub_email": true,
  "scrub_phone": true,
  "scrub_ip": true,
  "custom_patterns": []
}
```

---

## 💡 Integration Examples

### **1. Scrub Tool Outputs (MCP Server)**

```python
from app.services.credential_scrubbing import scrub_credentials

async def call_tool(tool_name: str, input_data: dict):
    result = await tool_handler.execute(tool_name, input_data)

    # Scrub sensitive data from result
    if isinstance(result, dict):
        result = scrub_credentials(result)

    return result
```

---

### **2. Scrub Conversation History**

```python
from app.services.credential_scrubbing import scrub_credentials

def get_conversation_history(session_id: str):
    history = db.query(ConversationHistory).filter(
        ConversationHistory.session_id == session_id
    ).all()

    # Scrub all entries
    scrubbed_history = []
    for entry in history:
        scrubbed_history.append({
            "tool_name": entry.tool_name,
            "input": scrub_credentials(entry.input),
            "output": scrub_credentials(entry.output)
        })

    return scrubbed_history
```

---

### **3. Scrub Audit Logs**

```python
from app.services.credential_scrubbing import CredentialScrubber

scrubber = CredentialScrubber()

def log_approval(entry: ApprovalLogEntry):
    # Scrub before logging
    scrubbed_entry = scrubber.scrub_log_entry({
        "session_id": entry.session_id,
        "tool_name": entry.tool_name,
        "input": entry.input_data,
        "output": entry.output_data
    })

    # Log scrubbed entry
    audit_logger.info(scrubbed_entry)
```

---

### **4. Scrub Error Messages**

```python
from app.services.credential_scrubbing import scrub_credentials

def handle_error(error: Exception):
    error_msg = str(error)

    # Scrub sensitive data from error messages
    # (e.g., "API key sk-ant-123 invalid" -> "API key ***REDACTED*** invalid")
    clean_msg = scrub_credentials(error_msg)

    logger.error(clean_msg)
    return clean_msg
```

---

### **5. Custom Patterns**

```python
from app.services.credential_scrubbing import CredentialScrubber

# Add custom regex pattern
scrubber = CredentialScrubber(config={
    "custom_patterns": [
        r'(CUSTOM_TOKEN_[A-Z0-9]{32})',  # Custom token format
        r'(internal_id_\d{10})'           # Internal IDs
    ]
})

# Use custom scrubber
clean = scrubber.scrub("Token: CUSTOM_TOKEN_ABC1234567890XYZ1234567890XYZ")
# Result: "Token: ***REDACTED***"
```

---

## 🎨 Advanced Features

### **Context Preservation**

The scrubber preserves JSON key names and field labels:

```python
# Input
{"password": "secret123", "api_key": "sk-ant-123"}

# Output (keys preserved, values redacted)
{"password": "***REDACTED***", "api_key": "***REDACTED***"}
```

---

### **Recursive Scrubbing**

Automatically scrubs nested dictionaries and lists:

```python
data = {
    "user": {
        "name": "John",
        "credentials": {
            "api_key": "sk-ant-123",
            "password": "secret"
        }
    },
    "contacts": [
        {"email": "agent@example.com"},
        {"phone": "+1-415-555-1234"}
    ]
}

clean = scrub_credentials(data)
# Result: {
#   "user": {
#     "name": "John",
#     "credentials": {
#       "api_key": "***REDACTED***",
#       "password": "***REDACTED***"
#     }
#   },
#   "contacts": [
#     {"email": "age***REDACTED***"},
#     {"phone": "***REDACTED***"}
#   ]
# }
```

---

### **Sensitive Key Detection**

Automatically detects sensitive dictionary keys:

```python
data = {
    "password": "secret123",      # Redacted (sensitive key)
    "api_key": "sk-ant-123",      # Redacted (sensitive key)
    "secret_token": "abc123",     # Redacted (sensitive key)
    "name": "John",               # Kept (not sensitive)
    "description": "API key is sk-ant-456 in prod"  # Value also scrubbed
}

clean = scrub_credentials(data)
# Result: {
#   "password": "***REDACTED***",
#   "api_key": "***REDACTED***",
#   "secret_token": "***REDACTED***",
#   "name": "John",
#   "description": "API key is ***REDACTED*** in prod"
# }
```

---

## 🔒 Security Best Practices

### **1. Always Scrub Before Logging**

```python
# ❌ BAD - Logs sensitive data
logger.info(f"API call with key: {api_key}")

# ✅ GOOD - Scrubs before logging
logger.info(f"API call with key: {scrub_credentials(api_key)}")
```

---

### **2. Scrub Error Messages**

```python
# ❌ BAD - May expose API keys in error messages
return {"error": str(exception)}

# ✅ GOOD - Scrub error messages
return {"error": scrub_credentials(str(exception))}
```

---

### **3. Scrub Audit Trails**

```python
# ❌ BAD - Stores sensitive data in audit log
audit_log.append({
    "tool": "send_contract",
    "input": input_data  # May contain passwords
})

# ✅ GOOD - Scrub before logging
audit_log.append({
    "tool": "send_contract",
    "input": scrub_credentials(input_data)
})
```

---

### **4. Scrub Conversation History**

```python
# ❌ BAD - Returns raw conversation history
return db.query(ConversationHistory).all()

# ✅ GOOD - Scrubs before returning
history = db.query(ConversationHistory).all()
for entry in history:
    entry.input = scrub_credentials(entry.input)
    entry.output = scrub_credentials(entry.output)
return history
```

---

### **5. Use Partial Redaction for Debugging**

```python
# Development mode: Keep 4 chars for debugging
if settings.DEBUG:
    clean = scrub_credentials(data, config={"keep_chars": 4})
    # "API key: sk-a***cdef" (still partially visible)

# Production mode: Full redaction
else:
    clean = scrub_credentials(data)
    # "API key: ***REDACTED***" (fully hidden)
```

---

## 🧪 Testing

### **Run Built-in Tests**

```bash
curl -X GET http://localhost:8000/scrub/test
```

**Expected output:**
```json
{
  "total_tests": 10,
  "passed": 10,
  "results": [...]
}
```

---

### **Test Custom Patterns**

```python
from app.services.credential_scrubbing import CredentialScrubber

# Create scrubber with custom pattern
scrubber = CredentialScrubber(config={
    "custom_patterns": [r'(MY_CUSTOM_TOKEN_\d{10})']
})

# Test it
input_text = "Token: MY_CUSTOM_TOKEN_1234567890"
output_text = scrubber.scrub(input_text)

assert output_text == "Token: ***REDACTED***"
assert "MY_CUSTOM_TOKEN_1234567890" not in output_text
```

---

## 🎯 Use Cases

### **1. MCP Tool Output Sanitization**

Every MCP tool output should be scrubbed before returning to the user:

```python
@mcp_tool()
def send_contract(property_id: int, contract_id: int):
    result = contract_service.send(property_id, contract_id)

    # Scrub sensitive data from result
    result["response"] = scrub_credentials(result["response"])

    return result
```

---

### **2. Conversation History Export**

When exporting conversation history for analysis:

```python
def export_conversation_history(session_id: str):
    history = get_conversation_history(session_id)

    # Scrub all entries
    scrubbed_history = [
        scrub_credentials(entry) for entry in history
    ]

    # Write to file
    with open(f"history_{session_id}.json", "w") as f:
        json.dump(scrubbed_history, f, indent=2)
```

---

### **3. Audit Trail Compliance**

For compliance and security auditing:

```python
def log_tool_execution(tool_name: str, input_data: dict, output_data: dict):
    # Scrub before logging
    log_entry = {
        "timestamp": datetime.now(),
        "tool": tool_name,
        "input": scrub_credentials(input_data),
        "output": scrub_credentials(output_data)
    }

    # Write to audit log
    audit_logger.info(json.dumps(log_entry))
```

---

### **4. Error Monitoring**

When sending errors to monitoring services (Sentry, DataDog, etc.):

```python
import sentry_sdk

def capture_exception(exception: Exception):
    # Scrub error message
    clean_message = scrub_credentials(str(exception))

    # Send to Sentry
    sentry_sdk.capture_exception(
        Exception(clean_message)
    )
```

---

## ⚙️ Configuration

### **Environment Variables** (Optional)

```bash
# .env
CREDENTIAL_SCRUBBER_REDACTION_STRING="***REDACTED***"
CREDENTIAL_SCRUBBER_KEEP_CHARS=0
CREDENTIAL_SCRUBBER_SCRUB_EMAIL=true
CREDENTIAL_SCRUBBER_SCRUB_PHONE=true
CREDENTIAL_SCRUBBER_SCRUB_IP=true
```

---

### **Code Configuration**

```python
from app.services.credential_scrubbing import CredentialScrubber

# Custom scrubber
custom_scrubber = CredentialScrubber(config={
    "redaction_string": "[HIDDEN]",  # Custom redaction string
    "keep_chars": 4,                 # Keep 4 leading/trailing chars
    "scrub_email": False,            # Don't scrub emails
    "scrub_phone": False,            # Don't scrub phone numbers
    "scrub_ip": False,               # Don't scrub IP addresses
    "custom_patterns": [             # Custom regex patterns
        r'(INTERNAL_TOKEN_\w{32})',
        r'(SECRET_ID_\d{10})'
    ]
})
```

---

## ✅ Summary

**Credential Scrubbing provides:**

✅ **Automatic detection** of API keys, passwords, tokens, SSNs, credit cards
✅ **Context preservation** — JSON keys and labels kept intact
✅ **Recursive scrubbing** — Nested dicts and lists handled automatically
✅ **Sensitive key detection** — Detects sensitive dictionary keys
✅ **Partial redaction** — Keep leading/trailing chars for debugging
✅ **Custom patterns** — Add your own regex patterns
✅ **API endpoints** — Test and use via REST API
✅ **Integration helpers** — Easy integration with logs, history, audit trails

**Integrate with:**
- MCP tool outputs
- Conversation history
- Audit logs
- Error messages
- API responses
- File exports

**Prevents accidental exposure of secrets!**

---

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)
