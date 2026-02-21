import enum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CommissionStatus(str, enum.Enum):
    PROJECTED = "projected"
    PENDING = "pending"
    INVOICED = "invoiced"
    PAID = "paid"


class Commission(Base):
    __tablename__ = "commissions"
    __table_args__ = (
        Index("ix_commissions_agent_id", "agent_id"),
        Index("ix_commissions_status", "status"),
        Index("ix_commissions_property_id", "property_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)

    sale_price = Column(Float, nullable=True)
    commission_rate = Column(Float, nullable=True)  # percentage, e.g., 3.0
    commission_amount = Column(Float, nullable=True)
    split_percentage = Column(Float, default=100.0)  # agent's share if split
    net_amount = Column(Float, nullable=True)

    status = Column(Enum(CommissionStatus), default=CommissionStatus.PROJECTED)
    notes = Column(Text, nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    agent = relationship("Agent")
    property = relationship("Property")
    transaction = relationship("Transaction", back_populates="commission")
    client = relationship("Client", back_populates="commissions")
