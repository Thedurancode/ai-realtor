# Real-Time Notifications System

## Overview

The AI Realtor platform now includes a comprehensive real-time notification system that broadcasts important events to the TV display via WebSockets. Notifications appear as animated toast messages and automatically dismiss after a configurable duration.

---

## Features

✅ **7 Notification Types**
- Contract Signed
- New Lead
- Property Price Change
- Property Status Change
- Appointment Reminders
- Skip Trace Complete
- Enrichment Complete

✅ **4 Priority Levels**
- Urgent (red)
- High (orange)
- Medium (blue)
- Low (gray)

✅ **Real-Time Delivery**
- WebSocket broadcasting
- Instant TV display updates
- Auto-dismiss with progress bar
- Beautiful animations (Framer Motion)

✅ **Persistent Storage**
- SQLite database storage
- Query notification history
- Mark as read/dismissed
- Filter by type/priority

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Backend Event                          │
│  (Contract signed, new lead, price change, etc.)           │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              NotificationService.notify_*()                 │
│  • Creates notification in database                         │
│  • Broadcasts via WebSocket manager                         │
└────────────────────────┬────────────────────────────────────┘
                         ↓
           ┌─────────────┴─────────────┐
           ↓                           ↓
┌──────────────────────┐    ┌─────────────────────────┐
│   SQLite Database    │    │  WebSocket Broadcast    │
│  (notifications)     │    │  {"action": "notification"}│
└──────────────────────┘    └────────┬────────────────┘
                                     ↓
                         ┌───────────────────────────┐
                         │  Frontend (page.tsx)     │
                         │  useAgentStore.addNotification()│
                         └───────────┬───────────────┘
                                     ↓
                         ┌───────────────────────────┐
                         │  NotificationToast.tsx   │
                         │  • Animated toast        │
                         │  • Auto-dismiss timer    │
                         │  • Priority coloring     │
                         └───────────────────────────┘
```

---

## API Endpoints

### List Notifications
```http
GET /notifications/?limit=50&unread_only=false
```

**Response:**
```json
[
  {
    "id": 1,
    "type": "contract_signed",
    "priority": "high",
    "title": "✅ Contract Fully Signed!",
    "message": "All parties signed Purchase Agreement for 123 Main St",
    "property_id": 5,
    "icon": "✅",
    "is_read": false,
    "is_dismissed": false,
    "created_at": "2026-02-04T20:15:30.123456"
  }
]
```

### Create Custom Notification
```http
POST /notifications/
Content-Type: application/json

{
  "type": "general",
  "priority": "high",
  "title": "🎉 Milestone Reached",
  "message": "You've closed 10 deals this month!",
  "icon": "🎉",
  "auto_dismiss_seconds": 10
}
```

### Mark as Read
```http
POST /notifications/{notification_id}/read
```

### Dismiss Notification
```http
POST /notifications/{notification_id}/dismiss
```

### Delete Notification
```http
DELETE /notifications/{notification_id}
```

---

## Demo Endpoints

### Test Contract Signed
```http
POST /notifications/demo/contract-signed
```

### Test New Lead
```http
POST /notifications/demo/new-lead
```

### Test Price Change
```http
POST /notifications/demo/price-change
```

### Test Appointment
```http
POST /notifications/demo/appointment
```

---

## Notification Types

### 1. Contract Signed
**Triggers:**
- When contract status changes to "completed"
- Via DocuSeal webhook
- Manual status refresh

**Data:**
```python
await notification_service.notify_contract_signed(
    db=db,
    manager=manager,
    contract_id=15,
    contract_name="Purchase Agreement",
    signer_name="John Smith",
    property_address="123 Main St",
    remaining_signers=0  # 0 = fully signed
)
```

---

### 2. New Lead
**Triggers:**
- When contact with role "buyer" or "seller" is created
- Via API or voice commands

**Data:**
```python
await notification_service.notify_new_lead(
    db=db,
    manager=manager,
    contact_id=23,
    contact_name="Sarah Johnson",
    contact_email="sarah@example.com",
    contact_phone="555-1234",
    property_address="456 Oak Ave",
    property_id=8,
    lead_source="Website Form"
)
```

---

### 3. Property Price Change
**Triggers:**
- When property price is updated via PATCH /properties/{id}

**Data:**
```python
await notification_service.notify_property_price_change(
    db=db,
    manager=manager,
    property_id=5,
    property_address="789 Park Lane",
    old_price=500000,
    new_price=475000,  # $25k reduction
    agent_id=1
)
```

---

### 4. Property Status Change
**Triggers:**
- When property status is updated (available → pending → sold)

**Data:**
```python
await notification_service.notify_property_status_change(
    db=db,
    manager=manager,
    property_id=5,
    property_address="789 Park Lane",
    old_status="available",
    new_status="pending",
    agent_id=1
)
```

---

### 5. Appointment Reminder
**Triggers:**
- Manually via API (can be automated with scheduler)

**Data:**
```python
await notification_service.notify_appointment_reminder(
    db=db,
    manager=manager,
    appointment_type="Property Showing",
    appointment_time="2:00 PM",
    property_address="321 Elm Street",
    property_id=12,
    client_name="Mike & Lisa Chen",
    minutes_until=15,
    agent_id=1
)
```

---

### 6. Skip Trace Complete
**Triggers:**
- After successful skip trace operation

**Data:**
```python
await notification_service.notify_skip_trace_complete(
    db=db,
    manager=manager,
    property_id=5,
    property_address="123 Main St",
    owner_name="Robert Johnson",
    phone_count=2,
    email_count=1
)
```

---

### 7. Enrichment Complete
**Triggers:**
- After successful Zillow enrichment

**Data:**
```python
await notification_service.notify_enrichment_complete(
    db=db,
    manager=manager,
    property_id=5,
    property_address="123 Main St",
    zestimate=425000,
    photo_count=15
)
```

---

## Testing Notifications

### Using Test Script

```bash
# Test all notification types
python3 test_notifications.py all

# Test realistic sequence
python3 test_notifications.py sequence

# Test specific types
python3 test_notifications.py contract
python3 test_notifications.py lead
python3 test_notifications.py price
python3 test_notifications.py appointment

# List recent notifications
python3 test_notifications.py list
```

### Using curl

```bash
# Contract signed
curl -X POST http://localhost:8000/notifications/demo/contract-signed

# New lead
curl -X POST http://localhost:8000/notifications/demo/new-lead

# Price change
curl -X POST http://localhost:8000/notifications/demo/price-change

# Appointment
curl -X POST http://localhost:8000/notifications/demo/appointment

# Custom notification
curl -X POST http://localhost:8000/notifications/ \
  -H "Content-Type: application/json" \
  -d '{
    "type": "general",
    "priority": "urgent",
    "title": "⚠️ Action Required",
    "message": "Contract expires in 1 hour!",
    "icon": "⚠️",
    "auto_dismiss_seconds": 20
  }'
```

---

## Frontend Integration

### Zustand Store
```typescript
import { useAgentStore } from '@/store/useAgentStore'

function MyComponent() {
  const { notifications, dismissNotification } = useAgentStore()

  // notifications is an array of Notification objects
  // dismissNotification(id) removes a notification
}
```

### WebSocket Handler
Notifications are automatically received via WebSocket in `app/page.tsx`:

```typescript
ws.onmessage = (event) => {
  const command = JSON.parse(event.data)

  if (command.action === 'notification') {
    useAgentStore.getState().addNotification(command.notification)
  }
}
```

---

## Priority Colors

| Priority | Color       | Use Case                           |
|----------|-------------|-------------------------------------|
| Urgent   | Red         | Action required immediately         |
| High     | Orange      | Important but not time-sensitive    |
| Medium   | Blue        | Standard notifications              |
| Low      | Gray        | Informational only                  |

---

## Auto-Dismiss Behavior

```python
# Auto-dismiss after 10 seconds
notification = notification_service.create_notification(
    ...,
    auto_dismiss_seconds=10
)

# No auto-dismiss (stays until manually dismissed)
notification = notification_service.create_notification(
    ...,
    auto_dismiss_seconds=None
)
```

On the frontend:
- Progress bar shows time remaining
- Notification automatically removed when timer expires
- User can manually dismiss anytime

---

## Database Schema

```sql
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY,
    type VARCHAR NOT NULL,  -- contract_signed, new_lead, etc.
    priority VARCHAR NOT NULL,  -- urgent, high, medium, low
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    property_id INTEGER,
    contact_id INTEGER,
    contract_id INTEGER,
    agent_id INTEGER,
    data TEXT,  -- JSON string for extra data
    icon VARCHAR(50),
    action_url VARCHAR(500),
    is_read BOOLEAN DEFAULT FALSE,
    is_dismissed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,
    dismissed_at TIMESTAMP,
    auto_dismiss_seconds INTEGER
);
```

---

## Adding New Notification Types

### 1. Add to Enum (app/models/notification.py)
```python
class NotificationType(enum.Enum):
    # ... existing types ...
    NEW_TYPE = "new_type"
```

### 2. Create Service Method (app/services/notification_service.py)
```python
async def notify_new_type(
    self,
    db: Session,
    manager,
    # ... your parameters ...
):
    notification = self.create_notification(
        db=db,
        notification_type=NotificationType.NEW_TYPE,
        title="🔥 New Type Title",
        message="Your message here",
        priority=NotificationPriority.MEDIUM,
        icon="🔥",
        auto_dismiss_seconds=10
    )

    if manager:
        await manager.broadcast(self.get_websocket_payload(notification))

    return notification
```

### 3. Trigger from Router
```python
from app.services.notification_service import notification_service

# In your route handler
manager = get_ws_manager()
await notification_service.notify_new_type(
    db=db,
    manager=manager,
    # ... your data ...
)
```

---

## Best Practices

✅ **DO:**
- Use appropriate priority levels
- Keep titles concise (< 50 chars)
- Include relevant IDs (property_id, contract_id)
- Use emojis for visual distinction
- Set reasonable auto-dismiss times (5-15 seconds)

❌ **DON'T:**
- Send duplicate notifications
- Use urgent priority for non-critical items
- Create notifications for every API call
- Include sensitive data in messages
- Set auto_dismiss_seconds too short (<3s)

---

## Monitoring & Analytics

### Query Notification Stats
```python
from app.database import SessionLocal
from app.models.notification import Notification, NotificationType
from sqlalchemy import func

db = SessionLocal()

# Count by type
stats = db.query(
    Notification.type,
    func.count(Notification.id)
).group_by(Notification.type).all()

# Unread count
unread = db.query(Notification).filter(
    Notification.is_read == False
).count()

# Today's notifications
from datetime import datetime, timedelta
today = datetime.now() - timedelta(days=1)
today_notifs = db.query(Notification).filter(
    Notification.created_at >= today
).count()
```

---

## Troubleshooting

### Notifications not appearing on TV display

1. **Check backend is running:**
   ```bash
   curl http://localhost:8000/
   ```

2. **Check WebSocket connection:**
   Open browser console → Look for "WebSocket connected to backend"

3. **Test with demo endpoint:**
   ```bash
   curl -X POST http://localhost:8000/notifications/demo/contract-signed
   ```

4. **Check Zustand store:**
   Open React DevTools → Check useAgentStore → notifications array

### Notifications dismissed too quickly

Increase `auto_dismiss_seconds`:
```python
auto_dismiss_seconds=15  # Instead of 10
```

### Database errors

Run migrations:
```bash
# Backend will auto-create tables on startup
python3 -m uvicorn app.main:app --reload
```

---

## Future Enhancements

🔮 **Planned Features:**
- Notification sound effects
- Notification center (history panel)
- Email/SMS forwarding
- Notification groups (batch similar items)
- Custom notification templates
- Scheduled notifications
- Notification filtering (mute certain types)

---

**The notification system is fully operational and ready to use!** 🎉
