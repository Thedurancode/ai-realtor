"""
Compliance Rule Models - Knowledge base for state/local real estate regulations
"""
from enum import Enum
from sqlalchemy import Column, Index, Integer, String, Text, Boolean, Float, Date, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ComplianceCategory(str, Enum):
    """Categories of compliance rules"""
    DISCLOSURE = "disclosure"
    SAFETY = "safety"
    BUILDING_CODE = "building_code"
    ZONING = "zoning"
    ENVIRONMENTAL = "environmental"
    ACCESSIBILITY = "accessibility"
    LICENSING = "licensing"
    FAIR_HOUSING = "fair_housing"
    TAX = "tax"
    HOA = "hoa"
    OTHER = "other"


class RuleType(str, Enum):
    """Types of rule evaluation logic"""
    REQUIRED_FIELD = "required_field"      # Check if field exists
    THRESHOLD = "threshold"                # Numeric comparison
    DOCUMENT = "document"                  # Document must be uploaded
    AI_REVIEW = "ai_review"               # AI interprets complex rule
    BOOLEAN = "boolean"                    # True/false check
    LIST_CHECK = "list_check"             # Value must be in list
    DATE_RANGE = "date_range"             # Date must be within range
    CONDITIONAL = "conditional"            # If X then Y


class Severity(str, Enum):
    """Severity levels for rule violations"""
    CRITICAL = "critical"  # Blocks listing
    HIGH = "high"         # Must fix before listing
    MEDIUM = "medium"     # Should fix
    LOW = "low"          # Nice to have
    INFO = "info"        # Informational only


class ComplianceStatus(str, Enum):
    """Status of compliance check"""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class ViolationStatus(str, Enum):
    """Status of individual violation"""
    FAILED = "failed"
    WARNING = "warning"
    NEEDS_REVIEW = "needs_review"


class ComplianceRule(Base):
    """Compliance rules knowledge base"""
    __tablename__ = "compliance_rules"

    id = Column(Integer, primary_key=True, index=True)

    # Location (where rule applies)
    state = Column(String(2), nullable=False, index=True)
    city = Column(String(100), nullable=True, index=True)
    county = Column(String(100), nullable=True)
    applies_to_all_cities = Column(Boolean, default=True)

    # Rule identification
    rule_code = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "NY-LEAD-001"
    version = Column(Integer, default=1)
    parent_rule_id = Column(Integer, ForeignKey("compliance_rules.id"), nullable=True)

    # Categorization
    category = Column(String(50), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)
    tags = Column(JSON, default=list)  # ["lead", "pre-1978", "disclosure"]

    # Rule details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    legal_citation = Column(Text, nullable=True)  # e.g., "NY RPL § 462-a"
    source_url = Column(String(500), nullable=True)

    # Rule logic
    rule_type = Column(String(50), nullable=False)
    field_to_check = Column(String(100), nullable=True)
    condition = Column(String(255), nullable=True)
    threshold_value = Column(Float, nullable=True)
    allowed_values = Column(JSON, nullable=True)

    # AI-powered evaluation
    ai_prompt = Column(Text, nullable=True)
    use_ai_fallback = Column(Boolean, default=False)

    # Document requirements
    requires_document = Column(Boolean, default=False)
    document_type = Column(String(100), nullable=True)
    document_description = Column(Text, nullable=True)

    # Property filters
    property_type_filter = Column(JSON, nullable=True)
    min_price = Column(Float, nullable=True)
    max_price = Column(Float, nullable=True)
    min_year_built = Column(Integer, nullable=True)
    max_year_built = Column(Integer, nullable=True)

    # Severity & consequences
    severity = Column(String(20), nullable=False, default="medium")
    penalty_description = Column(Text, nullable=True)
    fine_amount_min = Column(Float, nullable=True)
    fine_amount_max = Column(Float, nullable=True)

    # Remediation
    how_to_fix = Column(Text, nullable=True)
    estimated_fix_cost = Column(Float, nullable=True)
    estimated_fix_time_days = Column(Integer, nullable=True)

    # Status & lifecycle
    is_active = Column(Boolean, default=True, index=True)
    is_draft = Column(Boolean, default=False)
    effective_date = Column(Date, nullable=True)
    expiration_date = Column(Date, nullable=True)

    # Metadata
    created_by = Column(Integer, ForeignKey("agents.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # Statistics
    times_checked = Column(Integer, default=0)
    times_violated = Column(Integer, default=0)

    # Relationships
    created_by_agent = relationship("Agent", foreign_keys=[created_by])
    previous_versions = relationship(
        "ComplianceRule",
        remote_side=[id],
        backref="parent_rule",
        foreign_keys=[parent_rule_id]
    )


class ComplianceCheck(Base):
    """Record of compliance checks run on properties"""
    __tablename__ = "compliance_checks"
    __table_args__ = (
        Index("ix_compliance_checks_property_id", "property_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)

    check_type = Column(String(50), default="full")
    status = Column(String(20), nullable=False)

    total_rules_checked = Column(Integer, default=0)
    passed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)

    completion_time_seconds = Column(Float, nullable=True)
    ai_summary = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    property = relationship("Property", backref="compliance_checks")
    agent = relationship("Agent", foreign_keys=[agent_id])
    violations = relationship("ComplianceViolation", back_populates="check", cascade="all, delete-orphan")


class ComplianceViolation(Base):
    """Individual rule violations found"""
    __tablename__ = "compliance_violations"

    id = Column(Integer, primary_key=True, index=True)
    check_id = Column(Integer, ForeignKey("compliance_checks.id"), nullable=False)
    rule_id = Column(Integer, ForeignKey("compliance_rules.id"), nullable=False)

    status = Column(String(20), nullable=False)
    severity = Column(String(20), nullable=False)

    violation_message = Column(Text, nullable=False)
    ai_explanation = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)

    expected_value = Column(String(255), nullable=True)
    actual_value = Column(String(255), nullable=True)

    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    check = relationship("ComplianceCheck", back_populates="violations")
    rule = relationship("ComplianceRule")


class ComplianceRuleTemplate(Base):
    """Templates for common rule patterns"""
    __tablename__ = "compliance_rule_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    rule_type = Column(String(50), nullable=False)
    template_json = Column(JSON, nullable=False)
    category = Column(String(50))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
