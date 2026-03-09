"""Transaction Coordinator — tracks deal milestones from accepted offer to closing."""

from sqlalchemy import Column, Index, Integer, String, DateTime, ForeignKey, Enum, Text, Boolean, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class TransactionStatus(str, enum.Enum):
    INITIATED = "initiated"
    ATTORNEY_REVIEW = "attorney_review"
    INSPECTIONS = "inspections"
    APPRAISAL = "appraisal"
    MORTGAGE_CONTINGENCY = "mortgage_contingency"
    TITLE_SEARCH = "title_search"
    FINAL_WALKTHROUGH = "final_walkthrough"
    CLOSING_SCHEDULED = "closing_scheduled"
    CLOSED = "closed"
    FELL_THROUGH = "fell_through"
    CANCELLED = "cancelled"


class MilestoneStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    WAIVED = "waived"
    FAILED = "failed"


class PartyRole(str, enum.Enum):
    BUYER = "buyer"
    SELLER = "seller"
    BUYER_AGENT = "buyer_agent"
    SELLER_AGENT = "seller_agent"
    ATTORNEY = "attorney"
    LENDER = "lender"
    TITLE_COMPANY = "title_company"
    INSPECTOR = "inspector"
    APPRAISER = "appraiser"


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_property_id", "property_id"),
        Index("ix_transactions_status", "status"),
        Index("ix_transactions_closing_date", "closing_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=True)

    status = Column(Enum(TransactionStatus), default=TransactionStatus.INITIATED, nullable=False)
    title = Column(String, nullable=False)

    # Key dates
    accepted_date = Column(DateTime(timezone=True), nullable=True)
    attorney_review_deadline = Column(DateTime(timezone=True), nullable=True)
    inspection_deadline = Column(DateTime(timezone=True), nullable=True)
    appraisal_deadline = Column(DateTime(timezone=True), nullable=True)
    mortgage_contingency_date = Column(DateTime(timezone=True), nullable=True)
    title_clear_date = Column(DateTime(timezone=True), nullable=True)
    final_walkthrough_date = Column(DateTime(timezone=True), nullable=True)
    closing_date = Column(DateTime(timezone=True), nullable=True)

    # Deal terms
    sale_price = Column(Float, nullable=True)
    earnest_money = Column(Float, nullable=True)
    commission_rate = Column(Float, nullable=True)
    financing_type = Column(String, nullable=True)  # cash, conventional, FHA, VA

    # Parties (JSON: list of {name, role, email, phone})
    parties = Column(JSON, default=list)

    # Notes & metadata
    notes = Column(Text, nullable=True)
    risk_flags = Column(JSON, default=list)  # ["appraisal_gap_risk", "slow_lender"]
    extra_data = Column(JSON, default=dict)

    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    property = relationship("Property", backref="transactions")
    offer = relationship("Offer", backref="transaction")
    milestones = relationship("TransactionMilestone", back_populates="transaction", cascade="all, delete-orphan", order_by="TransactionMilestone.due_date")


class TransactionMilestone(Base):
    __tablename__ = "transaction_milestones"
    __table_args__ = (
        Index("ix_milestones_transaction_id", "transaction_id"),
        Index("ix_milestones_status", "status"),
        Index("ix_milestones_due_date", "due_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(MilestoneStatus), default=MilestoneStatus.PENDING, nullable=False)

    # Responsibility
    assigned_role = Column(Enum(PartyRole), nullable=True)
    assigned_name = Column(String, nullable=True)
    assigned_contact = Column(String, nullable=True)  # email or phone

    # Timing
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    reminder_sent = Column(Boolean, default=False)

    # Outcome
    outcome_notes = Column(Text, nullable=True)
    documents = Column(JSON, default=list)  # list of doc references

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    transaction = relationship("Transaction", back_populates="milestones")
