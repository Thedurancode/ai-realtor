"""
Contract Template Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.models.contract_template import ContractCategory, ContractRequirement


class ContractTemplateBase(BaseModel):
    """Base contract template schema"""
    name: str = Field(..., description="Template name")
    description: Optional[str] = None
    category: ContractCategory
    requirement: ContractRequirement = ContractRequirement.RECOMMENDED

    # DocuSeal integration
    docuseal_template_id: Optional[str] = None
    docuseal_template_name: Optional[str] = None

    # Filters
    state: Optional[str] = Field(None, min_length=2, max_length=2)
    city: Optional[str] = None
    property_type_filter: Optional[List[str]] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    deal_type_filter: Optional[List[str]] = None

    # Configuration
    auto_attach_on_create: bool = True
    auto_send: bool = False
    default_recipient_role: Optional[str] = None
    required_signer_roles: Optional[List[str]] = None
    message_template: Optional[str] = None

    is_active: bool = True
    priority: int = 0


class ContractTemplateCreate(ContractTemplateBase):
    """Create contract template"""
    pass


class ContractTemplateUpdate(BaseModel):
    """Update contract template"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[ContractCategory] = None
    requirement: Optional[ContractRequirement] = None
    docuseal_template_id: Optional[str] = None
    docuseal_template_name: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    property_type_filter: Optional[List[str]] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    deal_type_filter: Optional[List[str]] = None
    auto_attach_on_create: Optional[bool] = None
    auto_send: Optional[bool] = None
    default_recipient_role: Optional[str] = None
    required_signer_roles: Optional[List[str]] = None
    message_template: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None


class ContractTemplateResponse(ContractTemplateBase):
    """Contract template response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
