"""
Contact List Schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ListType:
    SMART = "smart"
    MANUAL = "manual"
    IMPORTED = "imported"
    CAMPAIGN = "campaign"


class SmartListRule:
    LAST_24_HOURS = "last_24_hours"
    LAST_2_DAYS = "last_2_days"
    LAST_7_DAYS = "last_7_days"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    NO_PROPERTY = "no_property"
    HAS_PROPERTY = "has_property"
    NO_PHONE = "no_phone"
    HAS_EMAIL = "has_email"
    UNSCONTACTED = "uncontacted"


# ============================================================================
# CREATE
# ============================================================================

class ContactListCreate(BaseModel):
    """Create a new contact list"""
    name: str = Field(..., min_length=1, max_length=200, description="List name")
    description: Optional[str] = Field(None, description="List description")
    list_type: str = Field(ListType.MANUAL, description="Type of list")
    smart_rule: Optional[str] = Field(None, description="Smart list rule (if type=smart)")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters (city, state, etc.)")
    contact_ids: Optional[List[int]] = Field(None, description="Contact IDs (for manual lists)")
    campaign_id: Optional[int] = Field(None, description="Linked campaign ID (if type=campaign)")
    auto_refresh: bool = Field(True, description="Auto-refresh smart lists")
    refresh_interval_hours: int = Field(24, description="Refresh interval for smart lists")


class SmartListCreate(BaseModel):
    """Create a smart list with auto-population"""
    name: str = Field(..., min_length=1, max_length=200, description="List name")
    description: Optional[str] = Field(None, description="List description")
    smart_rule: str = Field(..., description="Auto-population rule")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters (city, state, etc.)")
    auto_refresh: bool = Field(True, description="Auto-refresh this smart list")
    refresh_interval_hours: int = Field(24, ge=1, le=168, description="Refresh interval (1-168 hours)")


class QuickSmartListCreate(BaseModel):
    """Quick-create smart list from preset"""
    preset: str = Field(
        ...,
        description="Preset name: 'interested_this_week', 'new_leads_2days', 'new_leads_7days', 'this_month', 'uncontacted'"
    )
    custom_name: Optional[str] = Field(None, description="Custom list name (overrides preset)")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters (city, state, etc.)")


# ============================================================================
# RESPONSE
# ============================================================================

class ContactListItem(BaseModel):
    """Contact list item for list views"""
    id: int
    name: str
    description: Optional[str]
    list_type: str
    smart_rule: Optional[str]
    total_contacts: int
    auto_refresh: bool
    last_refreshed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ContactListDetail(BaseModel):
    """Full contact list details with contacts"""
    id: int
    name: str
    description: Optional[str]
    list_type: str
    smart_rule: Optional[str]
    filters: Optional[Dict[str, Any]]
    contact_ids: Optional[List[int]]
    campaign_id: Optional[int]
    total_contacts: int
    auto_refresh: bool
    last_refreshed_at: Optional[datetime]
    refresh_interval_hours: int
    last_contact_added_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    contacts: Optional[List[Dict[str, Any]]] = None  # Contacts in list

    class Config:
        from_attributes = True


class SmartListPreset(BaseModel):
    """Smart list preset for quick creation"""
    name: str
    display_name: str
    description: str
    smart_rule: str
    suggested_name: str


# ============================================================================
# UPDATE
# ============================================================================

class ContactListUpdate(BaseModel):
    """Update contact list"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    smart_rule: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    contact_ids: Optional[List[int]] = None
    auto_refresh: Optional[bool] = None
    refresh_interval_hours: Optional[int] = Field(None, ge=1, le=168)


# ============================================================================
# VOICE SUMMARY
# ============================================================================

class ContactListVoiceSummary(BaseModel):
    """Voice-friendly summary for TTS"""
    id: int
    name: str
    list_type: str
    total_contacts: int
    voice_summary: str  # Pre-generated voice summary
    last_refreshed: Optional[str] = None


# ============================================================================
# PRESETS
# ============================================================================

SMART_LIST_PRESETS = [
    {
        "name": "interested_this_week",
        "display_name": "Interested This Week",
        "description": "Contacts added this week (auto-refreshes daily)",
        "smart_rule": SmartListRule.THIS_WEEK,
        "suggested_name": "Interested This Week"
    },
    {
        "name": "new_leads_2days",
        "display_name": "New Leads (Last 2 Days)",
        "description": "Contacts added in the last 48 hours",
        "smart_rule": SmartListRule.LAST_2_DAYS,
        "suggested_name": "New Leads - Last 2 Days"
    },
    {
        "name": "new_leads_7days",
        "display_name": "New Leads (Last 7 Days)",
        "description": "Contacts added in the last week",
        "smart_rule": SmartListRule.LAST_7_DAYS,
        "suggested_name": "New Leads - Last 7 Days"
    },
    {
        "name": "this_month",
        "display_name": "This Month",
        "description": "All contacts added this month",
        "smart_rule": SmartListRule.THIS_MONTH,
        "suggested_name": f"New Contacts - {datetime.now().strftime('%B %Y')}"
    },
    {
        "name": "uncontacted",
        "display_name": "Uncontacted Leads",
        "description": "Contacts that have never been contacted",
        "smart_rule": SmartListRule.UNSCONTACTED,
        "suggested_name": "Uncontacted Leads"
    },
    {
        "name": "no_phone",
        "display_name": "Missing Phone",
        "description": "Contacts without phone numbers",
        "smart_rule": SmartListRule.NO_PHONE,
        "suggested_name": "Missing Phone Numbers"
    },
    {
        "name": "has_email",
        "display_name": "Has Email",
        "description": "Contacts with email addresses",
        "smart_rule": SmartListRule.HAS_EMAIL,
        "suggested_name": "Contacts With Email"
    },
    {
        "name": "no_property",
        "display_name": "No Property Linked",
        "description": "Contacts not linked to any property",
        "smart_rule": SmartListRule.NO_PROPERTY,
        "suggested_name": "No Property Linked"
    },
]
