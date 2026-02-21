from sqlalchemy import Column, Index, Integer, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class SubmitterStatus(str, enum.Enum):
    PENDING = "pending"
    OPENED = "opened"
    COMPLETED = "completed"
    DECLINED = "declined"


class ContractSubmitter(Base):
    """
    Tracks individual submitters (signers) for a contract.
    Allows multi-party signing where owner, lawyer, and agent all need to sign.
    """
    __tablename__ = "contract_submitters"
    __table_args__ = (
        Index("ix_contract_submitters_contract_id", "contract_id"),
        Index("ix_contract_submitters_contact_id", "contact_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)

    # Submitter details
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    role = Column(String, nullable=False)  # DocuSeal role: "Owner", "Lawyer", "Agent", etc.

    # Order for sequential signing (1, 2, 3...)
    signing_order = Column(Integer, default=1)

    # Status tracking
    status = Column(Enum(SubmitterStatus), default=SubmitterStatus.PENDING)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # DocuSeal submitter details
    docuseal_submitter_id = Column(String, nullable=True)
    docuseal_submitter_slug = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    contract = relationship("Contract", back_populates="submitters")
    contact = relationship("Contact")
