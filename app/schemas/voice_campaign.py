from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class VoiceCampaignCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    call_purpose: str = Field(default="property_update", min_length=1, max_length=64)

    property_id: Optional[int] = None
    contact_roles: Optional[list[str]] = None

    max_attempts: int = Field(default=3, ge=1, le=10)
    retry_delay_minutes: int = Field(default=60, ge=1, le=10080)
    rate_limit_per_minute: int = Field(default=5, ge=1, le=120)

    assistant_overrides: Optional[dict[str, Any]] = None
    auto_enroll_from_filters: bool = False


class VoiceCampaignUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    call_purpose: Optional[str] = Field(default=None, min_length=1, max_length=64)

    property_id: Optional[int] = None
    contact_roles: Optional[list[str]] = None

    max_attempts: Optional[int] = Field(default=None, ge=1, le=10)
    retry_delay_minutes: Optional[int] = Field(default=None, ge=1, le=10080)
    rate_limit_per_minute: Optional[int] = Field(default=None, ge=1, le=120)

    assistant_overrides: Optional[dict[str, Any]] = None
    status: Optional[str] = None


class VoiceCampaignResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: str
    call_purpose: str

    property_id: Optional[int]
    contact_roles: Optional[list[str]]

    max_attempts: int
    retry_delay_minutes: int
    rate_limit_per_minute: int

    assistant_overrides: Optional[dict[str, Any]]

    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    last_run_at: Optional[datetime]

    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class VoiceCampaignTargetResponse(BaseModel):
    id: int
    campaign_id: int
    contact_id: Optional[int]
    property_id: Optional[int]
    contact_name: Optional[str]
    phone_number: str
    status: str
    attempts_made: int
    next_attempt_at: datetime
    last_attempt_at: Optional[datetime]
    last_call_id: Optional[str]
    last_call_status: Optional[str]
    last_disposition: Optional[str]
    last_error: Optional[str]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class VoiceCampaignTargetManualAddRequest(BaseModel):
    contact_ids: list[int] = Field(default_factory=list)
    phone_numbers: list[str] = Field(default_factory=list)
    property_id: Optional[int] = None


class VoiceCampaignTargetFilterAddRequest(BaseModel):
    property_id: Optional[int] = None
    contact_roles: Optional[list[str]] = None
    limit: int = Field(default=500, ge=1, le=5000)


class VoiceCampaignEnrollResponse(BaseModel):
    campaign_id: int
    requested: int
    added: int
    skipped_existing: int
    skipped_invalid: int


class VoiceCampaignAnalyticsResponse(BaseModel):
    campaign_id: int
    campaign_status: str
    totals: dict[str, int]
    success_rate: float
    avg_attempts: float
    last_run_at: Optional[datetime]


class VoiceCampaignProcessResponse(BaseModel):
    campaigns_scanned: int
    targets_processed: int
    calls_started: int
    retries_scheduled: int
    exhausted: int
