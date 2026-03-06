"""
Email Triage Model — stores classified/triaged emails.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime

from app.database import Base


class TriagedEmail(Base):
    __tablename__ = "triaged_emails"

    id = Column(Integer, primary_key=True, index=True)
    gmail_id = Column(String, unique=True, nullable=True, index=True)
    from_address = Column(String, nullable=False)
    from_name = Column(String, nullable=True)
    subject = Column(String, nullable=False)
    body_preview = Column(String(500), nullable=True)
    classification = Column(String, nullable=False, index=True)  # hot_lead, warm_lead, contract_update, showing_request, spam, general
    priority = Column(Integer, nullable=False, default=3)  # 1 (highest) - 5 (lowest)
    drafted_response = Column(Text, nullable=True)
    response_sent = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
