from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChecklistItem(BaseModel):
    title: str
    description: str | None = None
    priority: str = "medium"  # low, medium, high, urgent
    due_days: int | None = None  # Days from deal type assignment


class DealTypeConfigBase(BaseModel):
    name: str = Field(..., description="Unique identifier (e.g., 'short_sale')")
    display_name: str = Field(..., description="Human-readable name (e.g., 'Short Sale')")
    description: str | None = None
    contract_templates: List[str] | None = None  # Template names to auto-attach
    required_contact_roles: List[str] | None = None  # ["buyer", "seller", "lender"]
    checklist: List[dict] | None = None  # [{title, description, priority, due_days}]
    compliance_tags: List[str] | None = None  # ["title_search", "bank_approval"]


class DealTypeConfigCreate(DealTypeConfigBase):
    pass


class DealTypeConfigUpdate(BaseModel):
    display_name: str | None = None
    description: str | None = None
    contract_templates: List[str] | None = None
    required_contact_roles: List[str] | None = None
    checklist: List[dict] | None = None
    compliance_tags: List[str] | None = None
    is_active: bool | None = None


class DealTypeConfigResponse(DealTypeConfigBase):
    id: int
    is_builtin: bool = False
    is_active: bool = True
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
