import enum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    UNDER_CONTRACT = "under_contract"
    INSPECTION = "inspection"
    APPRAISAL = "appraisal"
    TITLE_REVIEW = "title_review"
    FINANCING = "financing"
    CLOSING_SCHEDULED = "closing_scheduled"
    CLOSED = "closed"
    FELL_THROUGH = "fell_through"


class MilestoneStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WAIVED = "waived"
    FAILED = "failed"


class TransactionMilestone(Base):
    __tablename__ = "transaction_milestones"
    __table_args__ = (
        Index("ix_milestones_transaction_id", "transaction_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(MilestoneStatus), default=MilestoneStatus.PENDING)
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    transaction = relationship("Transaction", back_populates="milestones")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_property_id", "property_id"),
        Index("ix_transactions_status", "status"),
        Index("ix_transactions_agent_id", "agent_id"),
        Index("ix_transactions_closing_date", "closing_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=True)

    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    sale_price = Column(Float, nullable=True)
    closing_date = Column(DateTime(timezone=True), nullable=True)
    earnest_money = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    # Key contacts for the deal
    escrow_company = Column(String, nullable=True)
    title_company = Column(String, nullable=True)
    lender_name = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    property = relationship("Property")
    agent = relationship("Agent")
    client = relationship("Client", back_populates="transactions")
    offer = relationship("Offer")
    milestones = relationship("TransactionMilestone", back_populates="transaction", order_by="TransactionMilestone.sort_order")
    commission = relationship("Commission", back_populates="transaction", uselist=False)
