"""
Compliance Schemas - Pydantic models for request/response
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


# ========== COMPLIANCE RULE SCHEMAS ==========

class ComplianceRuleBase(BaseModel):
    """Base schema for compliance rules"""
    state: str = Field(..., min_length=2, max_length=2, description="2-letter state code")
    city: Optional[str] = None
    county: Optional[str] = None
    applies_to_all_cities: bool = True

    rule_code: str = Field(..., description="Unique rule code (e.g., NY-LEAD-001)")
    category: str
    subcategory: Optional[str] = None
    tags: List[str] = []

    title: str = Field(..., max_length=255)
    description: str
    legal_citation: Optional[str] = None
    source_url: Optional[str] = None

    rule_type: str
    field_to_check: Optional[str] = None
    condition: Optional[str] = None
    threshold_value: Optional[float] = None
    allowed_values: Optional[List[str]] = None

    ai_prompt: Optional[str] = None
    use_ai_fallback: bool = False

    requires_document: bool = False
    document_type: Optional[str] = None
    document_description: Optional[str] = None

    property_type_filter: Optional[List[str]] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_year_built: Optional[int] = None
    max_year_built: Optional[int] = None

    severity: str = "medium"
    penalty_description: Optional[str] = None
    fine_amount_min: Optional[float] = None
    fine_amount_max: Optional[float] = None

    how_to_fix: Optional[str] = None
    estimated_fix_cost: Optional[float] = None
    estimated_fix_time_days: Optional[int] = None

    is_active: bool = True
    is_draft: bool = False
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None


class ComplianceRuleCreate(ComplianceRuleBase):
    """Schema for creating a new compliance rule"""
    pass


class ComplianceRuleUpdate(BaseModel):
    """Schema for updating a compliance rule (all fields optional)"""
    state: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    applies_to_all_cities: Optional[bool] = None

    category: Optional[str] = None
    subcategory: Optional[str] = None
    tags: Optional[List[str]] = None

    title: Optional[str] = None
    description: Optional[str] = None
    legal_citation: Optional[str] = None
    source_url: Optional[str] = None

    rule_type: Optional[str] = None
    field_to_check: Optional[str] = None
    condition: Optional[str] = None
    threshold_value: Optional[float] = None
    allowed_values: Optional[List[str]] = None

    ai_prompt: Optional[str] = None
    use_ai_fallback: Optional[bool] = None

    requires_document: Optional[bool] = None
    document_type: Optional[str] = None
    document_description: Optional[str] = None

    property_type_filter: Optional[List[str]] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_year_built: Optional[int] = None
    max_year_built: Optional[int] = None

    severity: Optional[str] = None
    penalty_description: Optional[str] = None
    fine_amount_min: Optional[float] = None
    fine_amount_max: Optional[float] = None

    how_to_fix: Optional[str] = None
    estimated_fix_cost: Optional[float] = None
    estimated_fix_time_days: Optional[int] = None

    is_active: Optional[bool] = None
    is_draft: Optional[bool] = None
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None


class ComplianceRuleResponse(ComplianceRuleBase):
    """Schema for compliance rule response"""
    id: int
    version: int
    parent_rule_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    last_reviewed_at: Optional[datetime] = None
    times_checked: int
    times_violated: int

    class Config:
        from_attributes = True


class ComplianceRuleAIGenerateRequest(BaseModel):
    """Request to generate rule from natural language using AI"""
    state: str = Field(..., min_length=2, max_length=2)
    natural_language_rule: str = Field(..., description="Natural language description of the rule")
    category: Optional[str] = None
    legal_citation: Optional[str] = None


# ========== COMPLIANCE CHECK SCHEMAS ==========

class ComplianceCheckResponse(BaseModel):
    """Schema for compliance check response"""
    id: int
    property_id: int
    agent_id: Optional[int] = None
    check_type: str
    status: str
    total_rules_checked: int
    passed_count: int
    failed_count: int
    warning_count: int
    completion_time_seconds: Optional[float] = None
    ai_summary: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ComplianceViolationResponse(BaseModel):
    """Schema for compliance violation response"""
    id: int
    check_id: int
    rule_id: int
    status: str
    severity: str
    violation_message: str
    ai_explanation: Optional[str] = None
    recommendation: Optional[str] = None
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    rule: Optional[ComplianceRuleResponse] = None

    class Config:
        from_attributes = True


class ComplianceCheckDetailResponse(ComplianceCheckResponse):
    """Detailed compliance check with violations"""
    violations: List[ComplianceViolationResponse] = []


# ========== VOICE SCHEMAS ==========

class ComplianceCheckVoiceRequest(BaseModel):
    """Voice request to run compliance check"""
    address_query: str = Field(..., description="Partial address to find property")
    check_type: Optional[str] = "full"


class ComplianceVoiceResponse(BaseModel):
    """Voice response for compliance operations"""
    check: ComplianceCheckResponse
    voice_confirmation: str
    voice_summary: str


# ========== TEMPLATE SCHEMAS ==========

class ComplianceRuleTemplateResponse(BaseModel):
    """Schema for rule template response"""
    id: int
    name: str
    description: Optional[str] = None
    rule_type: str
    template_json: dict
    category: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
