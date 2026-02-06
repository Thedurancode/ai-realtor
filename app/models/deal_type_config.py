from sqlalchemy import Column, Integer, String, Boolean, Text, JSON, DateTime
from sqlalchemy.sql import func

from app.database import Base


class DealTypeConfig(Base):
    __tablename__ = "deal_type_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)  # "short_sale" or custom name
    display_name = Column(String, nullable=False)  # "Short Sale"
    description = Column(Text, nullable=True)
    is_builtin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # What it triggers (all JSON arrays)
    contract_templates = Column(JSON, nullable=True)  # Template names to auto-attach
    required_contact_roles = Column(JSON, nullable=True)  # ["buyer", "seller", "lender"]
    checklist = Column(JSON, nullable=True)  # [{title, description, priority, due_days}]
    compliance_tags = Column(JSON, nullable=True)  # ["title_search", "bank_approval"]

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
