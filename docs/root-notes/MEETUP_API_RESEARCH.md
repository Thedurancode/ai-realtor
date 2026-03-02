# Meetup API Integration Research & Implementation Plan

## Executive Summary

**Can we integrate Meetup API to post events? YES**

Meetup has an official REST API that supports event creation, but there are some considerations:
- Requires OAuth 2.0 authentication
- Rate-limited (may need higher tier for frequent posting)
- Events must be associated with a Meetup group
- Requires venue and time details

---

## Meetup API Overview

### Base Info
- **API Version**: v3 (RESTful)
- **Base URL**: `https://api.meetup.com/v3/`
- **Authentication**: OAuth 2.0
- **Documentation**: `https://www.meetup.com/meetup_api/docs/`

### API Capabilities

| Feature | Endpoint | Method | Notes |
|---------|----------|--------|--------|
| **Create Events** | `/:urlname/events` | POST | Events must be linked to a group |
| **List Events** | `/:urlname/events` | GET | Get events from a group |
| **Get Event Details** | `/:urlname/events/:id` | GET | Full event information |
| **Update Events** | `/:urlname/events/:id` | PATCH | Modify existing events |
| **Delete Events** | `/:urlname/events/:id` | DELETE | Remove events |
| **Get Groups** | `/pro/:urlname/groups` | GET | List user's groups |
| **RSVP Management** | `/:urlname/events/:id/rsvps` | POST | RSVP to events |
| **Venues** | `/pro/:urlname/venues` | GET/POST | Manage venues |

---

## Integration Approach for AI Realtor

### Option 1: Direct API Integration (Recommended)

**Pros:**
- Full control over event creation
- Can attach venues, descriptions, images
- Automated RSVP tracking
- Custom event fields

**Cons:**
- Requires OAuth setup (complex)
- Rate limits apply
- Need Meetup Pro account for API access
- Events must be tied to a Meetup group

**Implementation:**

```python
# New service: app/services/meetup_service.py

class MeetupAPIClient:
    """Client for Meetup v3 API"""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.meetup.com/v3"

    async def create_event(
        self,
        group_urlname: str,
        title: str,
        description: str,
        start_time: str,  # ISO 8601
        duration: int,  # milliseconds
        venue_id: Optional[str] = None,
        event_hosts: Optional[List[dict]] = None
    ) -> dict:
        """Create event in Meetup group"""

        payload = {
            "title": title,
            "description": description,
            "start": start_time,
            "duration": duration,
            "time_zone": "America/New_York"
        }

        if venue_id:
            payload["venue"] = {"id": venue_id}

        if event_hosts:
            payload["event_hosts"] = event_hosts

        url = f"/{group_urlname}/events"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{url}",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
```

### Database Schema

```python
# app/models/meetup.py

class MeetupEvent(Base):
    """Track Meetup events synced with properties"""
    __tablename__ = "meetup_events"

    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)

    # Meetup event data
    meetup_event_id = Column(String(100), unique=True)
    group_urlname = Column(String(100))  # e.g., "CodeLive-Events"
    event_title = Column(String(255))
    event_description = Column(Text)

    # Event details
    start_time = Column(DateTime(timezone=True))
    duration_ms = Column(Integer)
    venue_id = Column(String(100))

    # RSVP tracking
    rsvp_count = Column(Integer, default=0)
    rsvp_limit = Column(Integer)

    # Sync status
    synced_at = Column(DateTime(timezone=True))
    status = Column(String(50))  # draft, published, cancelled

    # Relationships
    property = relationship("Property")
    agent = relationship("Agent")


class MeetupGroup(Base):
    """Track Meetup groups (for hosting events)"""
    __tablename__ = "meetup_groups"

    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))

    # Meetup group info
    group_urlname = Column(String(100), unique=True)
    group_name = Column(String(255))
    member_count = Column(Integer)

    # OAuth credentials
    access_token = Column(Text)  # Encrypted
    refresh_token = Column(Text)  # Encrypted
    token_expires_at = Column(DateTime(timezone=True))

    # Settings
    is_active = Column(Boolean, default=True)
    auto_post_events = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

### New API Endpoints

```python
# app/routers/meetup.py

router = APIRouter(prefix="/meetup", tags=["Meetup Integration"])

class MeetupEventCreate(BaseModel):
    """Create Meetup event from property/class"""
    group_urlname: str
    title: str
    description: str
    start_time: str  # ISO datetime
    duration_minutes: int
    venue_id: Optional[str] = None
    property_id: Optional[int] = None
    publish_to_social: bool = False


@router.post("/events/create")
async def create_meetup_event(
    event: MeetupEventCreate,
    agent_id: int,
    db: Session = Depends(get_db)
):
    """
    Create a Meetup event and optionally post to social media

    Example:
    POST /meetup/events/create
    {
        "group_urlname": "CodeLive-Events",
        "title": "CodeLive VibeCoding Class",
        "description": "Learn to code in a relaxed environment...",
        "start_time": "2026-02-22T14:00:00",
        "duration_minutes": 120,
        "property_id": null,
        "publish_to_social": true
    }
    """

    # Get Meetup group credentials
    group = db.query(MeetupGroup).filter(
        MeetupGroup.group_urlname == event.group_urlname,
        MeetupGroup.agent_id == agent_id
    ).first()

    if not group:
        raise HTTPException(
            status_code=404,
            detail=f"Meetup group '{event.group_urlname}' not found"
        )

    # Create event in Meetup
    client = MeetupAPIClient(group.access_token)

    meetup_event = await client.create_event(
        group_urlname=event.group_urlname,
        title=event.title,
        description=event.description,
        start_time=event.start_time,
        duration=event.duration_minutes * 60000,  # Convert to ms
        venue_id=event.venue_id
    )

    # Save to database
    db_event = MeetupEvent(
        agent_id=agent_id,
        property_id=event.property_id,
        meetup_event_id=meetup_event["id"],
        group_urlname=event.group_urlname,
        event_title=event.title,
        event_description=event.description,
        start_time=datetime.fromisoformat(event.start_time.replace('Z', '+00:00')),
        duration_ms=event.duration_minutes * 60000,
        status="published"
    )

    db.add(db_event)
    db.commit()

    # Optionally post to social media
    social_posts = []
    if event.publish_to_social:
        # Post to Twitter/X, LinkedIn, etc.
        social_posts = await _post_to_social_media(
            agent_id=agent_id,
            event=event,
            db=db
        )

    return {
        "meetup_event_id": meetup_event["id"],
        "event_url": f"https://meetup.com/{event.group_urlname}/events/{meetup_event['id']}/",
        "social_posts": social_posts,
        "voice_summary": f"Created Meetup event '{event.title}' and posted to social media."
    }
```

---

## OAuth 2.0 Setup Flow

### Step 1: Register Meetup App
1. Go to https://www.meetup.com/api/
2. Create new OAuth app
3. Get `client_id` and `client_secret`
4. Set redirect URI

### Step 2: Authorization Flow
```python
# Authorization URL
auth_url = (
    f"https://www.meetup.com/oauth/authorize/"
    f"?client_id={client_id}"
    f"&response_type=code"
    f"&redirect_uri={redirect_uri}"
)

# User authorizes → Get auth code
# Exchange for access token
token_response = requests.post(
    "https://www.meetup.com/oauth/access",
    data={
        "client_id": client_id,
        "client_secret": client_secret,
        "code": auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }
)

access_token = token_response.json()["access_token"]
```

### Step 3: Store Credentials
Store encrypted in database (never in code):
```python
from cryptography.fernet import Fernet

# Encrypt token
key = os.environ.get("ENCRYPTION_KEY")
f = Fernet(key)
encrypted_token = f.encrypt(access_token.encode())

# Save to database
group.access_token = encrypted_token.decode()
```

---

## API Limitations

### Rate Limits
| Tier | Requests/Hour | Cost |
|------|--------------|------|
| Free | 20/hr | $0 |
| Pro | 2,000/hr | $50/mo |
| Enterprise | 10,000/hr | Custom |

### Event Requirements
- **Required**: title, description, start_time, duration, group
- **Optional**: venue, event_hosts, featured_photo, fee_amount
- **Constraints**: Start time must be in future, duration must be reasonable

---

## Comparison: Meetup vs. Social Media

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MEETUP VS SOCIAL MEDIA POSTING                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  Feature              │ Meetup API           │ Social Media (Postiz)       │
├─────────────────────────────────────────────────────────────────────────────┤
│  Event Registration   │ ✅ Built-in RSVP       │ ❌ Manual comments         │
│  Venue Management    │ ✅ Venue database     │ ❌ Text description only    │
│  Calendar Integration  │ ✅ Google Calendar sync  │ ❌ Manual add            │
│  RSVP Tracking        │ ✅ Automatic count    │ ❌ No tracking            │
│  Event Discovery      │ ✅ Meetup directory   │ ❌ Platform-specific       │
│  Email Notifications  │ ✅ Auto to attendees   │ ❌ Requires setup         │
│  Ticket Sales         │ ✅ Built-in          │ ❌ Third-party needed       │
│  Community Building   │ ✅ Group members     │ ❌ Followers only           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Recommended Implementation Strategy

### Phase 1: Basic Integration (1-2 days)
1. Set up Meetup OAuth credentials
2. Create `MeetupEvent` model
3. Implement event creation endpoint
4. Test with sample event

### Phase 2: Social Media Sync (1 day)
1. Auto-post to Twitter/LinkedIn when Meetup created
2. Include Meetup event link in social posts
3. Track which social platforms posted

### Phase 3: Advanced Features (2-3 days)
1. RSVP notifications to agent
2. Auto-create events from property classes
3. Sync event updates back to Meetup
4. Analytics dashboard

---

## Example Workflow

```
User: "Create a Meetup event for CodeLive VibeCoding class"

System:
1. ✅ Creates Meetup event in "CodeLive-Events" group
2. ✅ Generates event description with AI
3. ✅ Sets date/time (Saturday 2pm)
4. ✅ Attaches venue (if provided)
5. ✅ Posts to Twitter/X
6. ✅ Posts to LinkedIn
7. ✅ Returns event link + social post links

Result:
🎯 Meetup: https://meetup.com/CodeLive-Events/events/123456789/
🐦 Twitter: https://x.com/codeliveai/status/123456
👔 LinkedIn: https://linkedin.com/posts/123456
```

---

## Voice Commands

```
"Create a Meetup event for CodeLive VibeCoding class this Saturday"
"Post the class to Meetup and social media"
"Create event: CodeLive VibeCoding at 2pm Saturday, 2 hours"
"List all my Meetup events"
"How many RSVPs for the VibeCoding event?"
```

---

## MCP Tools (6 new tools)

```python
create_meetup_event(group, title, description, time, duration)
list_meetup_events(group_urlname)
get_meetup_event_rsvps(event_id)
post_meetup_to_social(event_id)
sync_meetup_event_to_property(property_id)
get_meetup_analytics(group_urlname)
```

---

## Cost & Considerations

### Setup Costs
- Meetup Pro: $50/month (for 2,000 API calls/hr)
- Development: ~8 hours
- Maintenance: ~2 hours/month

### Benefits
- 🎯 Targeted audience (people interested in your topic)
- 📅 Built-in RSVP and calendar integration
- 👥 Meetup community discovery (330,000 groups)
- 📊 Attendance tracking
- 🔄 Event updates and notifications

### Best For
- **Classes/Workshops** - Perfect fit for VibeCoding
- **Networking Events** - Tech meetups
- **Open Houses** - Property tours
- **Webinars** - Online events

---

## Conclusion

**Should we integrate Meetup? YES**

For CodeLive VibeCoding classes specifically, Meetup is the ideal platform because:
1. Built-in RSVP tracking
2. Targeted audience (people searching for coding classes)
3. Calendar integration
4. Event discovery (people find YOU)
5. Community building (repeat attendees)

**Recommendation:** Add Meetup integration alongside your existing social media posting. This gives you maximum reach:
- **Meetup** → Event hosting + RSVPs + discovery
- **Twitter/LinkedIn/Instagram** → Promotion + awareness

Would you like me to start implementing the Meetup integration?
