"""
Contact List Models for organizing contacts into smart lists
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM

from app.database import Base
# Import DirectMailCampaign to avoid relationship resolution issues
from app.models.direct_mail import DirectMailCampaign  # noqa: F401


class ListType(str):
    """Contact list types"""
    SMART = "smart"          # Auto-populated based on criteria
    MANUAL = "manual"        # Manually curated
    IMPORTED = "imported"    # From CSV import
    CAMPAIGN = "campaign"    # Linked to direct mail campaign


class SmartListRule(str):
    """Smart list auto-population rules"""
    LAST_24_HOURS = "last_24_hours"
    LAST_2_DAYS = "last_2_days"
    LAST_7_DAYS = "last_7_days"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    NO_PROPERTY = "no_property"        # Contacts not linked to any property
    HAS_PROPERTY = "has_property"      # Contacts linked to a property
    NO_PHONE = "no_phone"              # Contacts without phone number
    HAS_EMAIL = "has_email"            # Contacts with email
    UNSCONTACTED = "uncontacted"       # Never contacted (no campaigns sent)


class ContactList(Base):
    """
    Contact lists for organizing contacts
    Can be manual, smart (auto-populated), or linked to campaigns
    """
    __tablename__ = "contact_lists"

    id = Column(Integer, primary_key=True, index=True)

    # Agent ownership
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)

    # List metadata
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    list_type = Column(ENUM(ListType.SMART, ListType.MANUAL, ListType.IMPORTED, ListType.CAMPAIGN, name="list_type"), default=ListType.MANUAL, nullable=False)

    # Smart list configuration
    smart_rule = Column(ENUM(
        SmartListRule.LAST_24_HOURS,
        SmartListRule.LAST_2_DAYS,
        SmartListRule.LAST_7_DAYS,
        SmartListRule.THIS_WEEK,
        SmartListRule.THIS_MONTH,
        SmartListRule.LAST_30_DAYS,
        SmartListRule.LAST_90_DAYS,
        SmartListRule.NO_PROPERTY,
        SmartListRule.HAS_PROPERTY,
        SmartListRule.NO_PHONE,
        SmartListRule.HAS_EMAIL,
        SmartListRule.UNSCONTACTED,
        name="smart_rule"
    ), nullable=True)

    # Additional filters (JSON for flexibility)
    filters = Column(JSON, nullable=True)
    # Examples: {"city": "Miami", "state": "FL", "property_type": "condo"}

    # List membership (for manual lists, for smart lists this is auto-calculated)
    contact_ids = Column(JSON, nullable=True)  # List[int]

    # Linked campaign (if list_type=campaign)
    campaign_id = Column(Integer, ForeignKey("direct_mail_campaigns.id"), nullable=True)

    # Auto-refresh settings (for smart lists)
    auto_refresh = Column(Boolean, default=True)
    last_refreshed_at = Column(DateTime, nullable=True)
    refresh_interval_hours = Column(Integer, default=24)  # How often to auto-refresh

    # Stats
    total_contacts = Column(Integer, default=0)
    last_contact_added_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agent = relationship("Agent", back_populates="contact_lists")
    campaign = relationship("DirectMailCampaign", back_populates="contact_lists")

    def __repr__(self):
        return f"<ContactList(id={self.id}, name='{self.name}', type={self.list_type})>"

    def get_contacts_query(self, db):
        """
        Get SQLAlchemy query for contacts in this list

        For smart lists, applies the rule dynamically
        For manual lists, returns contacts by ID
        """
        from app.models.contact import Contact

        if self.list_type == ListType.SMART and self.smart_rule:
            # Build dynamic query based on smart rule
            query = db.query(Contact).filter(Contact.agent_id == self.agent_id)

            # Apply time-based rules
            now = datetime.utcnow()
            if self.smart_rule == SmartListRule.LAST_24_HOURS:
                cutoff = now - timedelta(hours=24)
                query = query.filter(Contact.created_at >= cutoff)
            elif self.smart_rule == SmartListRule.LAST_2_DAYS:
                cutoff = now - timedelta(days=2)
                query = query.filter(Contact.created_at >= cutoff)
            elif self.smart_rule == SmartListRule.LAST_7_DAYS:
                cutoff = now - timedelta(days=7)
                query = query.filter(Contact.created_at >= cutoff)
            elif self.smart_rule == SmartListRule.THIS_WEEK:
                # Start of current week (Monday)
                days_since_monday = now.weekday()
                start_of_week = now - timedelta(days=days_since_monday)
                start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Contact.created_at >= start_of_week)
            elif self.smart_rule == SmartListRule.THIS_MONTH:
                # Start of current month
                start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Contact.created_at >= start_of_month)
            elif self.smart_rule == SmartListRule.LAST_30_DAYS:
                cutoff = now - timedelta(days=30)
                query = query.filter(Contact.created_at >= cutoff)
            elif self.smart_rule == SmartListRule.LAST_90_DAYS:
                cutoff = now - timedelta(days=90)
                query = query.filter(Contact.created_at >= cutoff)

            # Apply property-based rules
            elif self.smart_rule == SmartListRule.NO_PROPERTY:
                query = query.filter(Contact.property_id == None)
            elif self.smart_rule == SmartListRule.HAS_PROPERTY:
                query = query.filter(Contact.property_id != None)

            # Apply contact info rules
            elif self.smart_rule == SmartListRule.NO_PHONE:
                query = query.filter(Contact.phone == None)
            elif self.smart_rule == SmartListRule.HAS_EMAIL:
                query = query.filter(Contact.email != None)

            # Apply additional filters from JSON
            if self.filters:
                if "city" in self.filters:
                    query = query.filter(Contact.city.ilike(f"%{self.filters['city']}%"))
                if "state" in self.filters:
                    query = query.filter(Contact.state == self.filters['state'])
                if "zip_code" in self.filters:
                    query = query.filter(Contact.zip_code == self.filters['zip_code'])

            return query

        elif self.list_type in [ListType.MANUAL, ListType.IMPORTED, ListType.CAMPAIGN]:
            # Return contacts by ID
            if self.contact_ids:
                return db.query(Contact).filter(
                    Contact.id.in_(self.contact_ids),
                    Contact.agent_id == self.agent_id
                )
            else:
                return db.query(Contact).filter(False)  # Empty result

        return db.query(Contact).filter(False)

    def refresh_count(self, db):
        """Update total_contacts count based on current query"""
        query = self.get_contacts_query(db)
        self.total_contacts = query.count()
        self.last_refreshed_at = datetime.utcnow()

        # Update last contact added timestamp
        latest_contact = query.order_by(Contact.created_at.desc()).first()
        if latest_contact:
            self.last_contact_added_at = latest_contact.created_at

        db.commit()


# Add relationship to Agent model (would need to update agent.py)
# Add relationship to DirectMailCampaign model (would need to update direct_mail.py)
