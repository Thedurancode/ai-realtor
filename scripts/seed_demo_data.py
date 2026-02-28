#!/usr/bin/env python3
"""
Seed Demo Database - Fixed Version

Populates the database with realistic demo data for testing and showcasing:
- 3 agents (different cities: Miami, New York, Austin)
- 15 properties (various types and price ranges)
- 30 days of analytics events
- Contract templates
- Analytics alerts
- Sample notifications

Usage:
    python scripts/seed_demo_data.py
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from random import randint, choice, uniform
import asyncio

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.agent import Agent
from app.models.property import Property, PropertyType, PropertyStatus
from app.models.analytics_event import AnalyticsEvent
from app.models.contract import Contract, ContractStatus
from app.models.analytics_alert import AnalyticsAlertRule, AlertType, AlertOperator, AlertStatus
from app.models.notification import Notification, NotificationType, NotificationPriority
from app.models.contact import Contact, ContactRole


def create_demo_agents(db: Session) -> list[Agent]:
    """Create 3 demo agents in different cities."""
    agents = []

    agent_data = [
        {
            "name": "Sarah Johnson",
            "email": "sarah.johnson@miami-realtor.com",
            "phone": "+13055551234",
            "city": "Miami",
            "license_number": "FL1234567",
        },
        {
            "name": "Michael Chen",
            "email": "michael.chen@nyluxury.com",
            "phone": "+12125554321",
            "city": "New York",
            "license_number": "NY9876543",
        },
        {
            "name": "Emily Rodriguez",
            "email": "emily.rodriguez@austinhomes.com",
            "phone": "+15125551234",
            "city": "Austin",
            "license_number": "TX4567890",
        },
    ]

    for data in agent_data:
        # Check if agent already exists
        existing = db.query(Agent).filter(Agent.license_number == data["license_number"]).first()
        if existing:
            agents.append(existing)
        else:
            agent = Agent(**data)
            db.add(agent)
            agents.append(agent)

    db.commit()
    for agent in agents:
        db.refresh(agent)

    print(f"✓ Using {len(agents)} agents")
    return agents


def create_demo_properties(db: Session, agents: list[Agent]) -> list[Property]:
    """Create 15 demo properties across all agents."""
    properties = []

    property_templates = [
        # Miami properties (Sarah Johnson - agent[0])
        {
            "title": "Ocean Drive Luxury Condo",
            "address": "123 Ocean Drive, Miami Beach, FL 33139",
            "city": "Miami Beach",
            "state": "FL",
            "zip_code": "33139",
            "price": 850000,
            "property_type": PropertyType.CONDO,
            "bedrooms": 2,
            "bathrooms": 2,
            "square_feet": 1200,
        },
        {
            "title": "Sunset Harbour Waterfront Home",
            "address": "456 Sunset Harbour, Miami, FL 33133",
            "city": "Miami",
            "state": "FL",
            "zip_code": "33133",
            "price": 1250000,
            "property_type": PropertyType.HOUSE,
            "bedrooms": 4,
            "bathrooms": 3,
            "square_feet": 2800,
        },
        {
            "title": "Brickell Ave Townhouse",
            "address": "789 Brickell Ave, Miami, FL 33131",
            "city": "Miami",
            "state": "FL",
            "zip_code": "33131",
            "price": 450000,
            "property_type": PropertyType.TOWNHOUSE,
            "bedrooms": 3,
            "bathrooms": 2,
            "square_feet": 1800,
        },
        {
            "title": "Coral Gables Estate",
            "address": "321 Coral Way, Miami, FL 33134",
            "city": "Coral Gables",
            "state": "FL",
            "zip_code": "33134",
            "price": 2100000,
            "property_type": PropertyType.HOUSE,
            "bedrooms": 5,
            "bathrooms": 4,
            "square_feet": 4200,
        },
        {
            "title": "Key Biscayne Beach Condo",
            "address": "555 Key Biscayne, Miami, FL 33149",
            "city": "Miami",
            "state": "FL",
            "zip_code": "33149",
            "price": 675000,
            "property_type": PropertyType.CONDO,
            "bedrooms": 2,
            "bathrooms": 2,
            "square_feet": 1350,
        },
        # New York properties (Michael Chen - agent[1])
        {
            "title": "Manhattan Penthouse",
            "address": "100 5th Avenue, New York, NY 10003",
            "city": "New York",
            "state": "NY",
            "zip_code": "10003",
            "price": 3500000,
            "property_type": PropertyType.CONDO,
            "bedrooms": 3,
            "bathrooms": 3,
            "square_feet": 2500,
        },
        {
            "title": "Brooklyn Brownstone",
            "address": "245 Park Avenue, Brooklyn, NY 11226",
            "city": "Brooklyn",
            "state": "NY",
            "zip_code": "11226",
            "price": 1800000,
            "property_type": PropertyType.HOUSE,
            "bedrooms": 4,
            "bathrooms": 3,
            "square_feet": 3200,
        },
        {
            "title": "Upper East Side Co-op",
            "address": "450 E 86th St, New York, NY 10028",
            "city": "New York",
            "state": "NY",
            "zip_code": "10028",
            "price": 950000,
            "property_type": PropertyType.APARTMENT,
            "bedrooms": 2,
            "bathrooms": 1,
            "square_feet": 1100,
        },
        {
            "title": "SoHo Artist Loft",
            "address": "155 Wooster St, New York, NY 10012",
            "city": "New York",
            "state": "NY",
            "zip_code": "10012",
            "price": 1450000,
            "property_type": PropertyType.APARTMENT,
            "bedrooms": 1,
            "bathrooms": 1,
            "square_feet": 1800,
        },
        {
            "title": "Tribeca Luxury Condo",
            "address": "101 Warren St, New York, NY 10007",
            "city": "New York",
            "state": "NY",
            "zip_code": "10007",
            "price": 2200000,
            "property_type": PropertyType.CONDO,
            "bedrooms": 2,
            "bathrooms": 2,
            "square_feet": 1600,
        },
        # Austin properties (Emily Rodriguez - agent[2])
        {
            "title": "Downtown Austin High-Rise",
            "address": "360 Condos, Austin, TX 78701",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701",
            "price": 550000,
            "property_type": PropertyType.CONDO,
            "bedrooms": 1,
            "bathrooms": 1,
            "square_feet": 950,
        },
        {
            "title": "Tarrytown Mansion",
            "address": "231 Westlake Dr, Austin, TX 78746",
            "city": "West Lake Hills",
            "state": "TX",
            "zip_code": "78746",
            "price": 1500000,
            "property_type": PropertyType.HOUSE,
            "bedrooms": 4,
            "bathrooms": 3,
            "square_feet": 3500,
        },
        {
            "title": "East Austin Bungalow",
            "address": "456 Rainey Street, Austin, TX 78701",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701",
            "price": 425000,
            "property_type": PropertyType.HOUSE,
            "bedrooms": 2,
            "bathrooms": 2,
            "square_feet": 1400,
        },
        {
            "title": "Domain Apartment",
            "address": "567 Domain, Austin, TX 78701",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701",
            "price": 375000,
            "property_type": PropertyType.APARTMENT,
            "bedrooms": 1,
            "bathrooms": 1,
            "square_feet": 750,
        },
        {
            "title": "South Austin Family Home",
            "address": "789 S Lamar Blvd, Austin, TX 78704",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78704",
            "price": 685000,
            "property_type": PropertyType.HOUSE,
            "bedrooms": 3,
            "bathrooms": 2,
            "square_feet": 2100,
        },
    ]

    # Assign properties to agents
    for i, template in enumerate(property_templates):
        agent = agents[i % len(agents)]
        template["agent_id"] = agent.id
        template["status"] = PropertyStatus.NEW_PROPERTY
        template["created_at"] = datetime.now(timezone.utc)

        property = Property(**template)
        db.add(property)
        properties.append(property)

    db.commit()
    for prop in properties:
        db.refresh(prop)

    print(f"✓ Created {len(properties)} demo properties")
    return properties


def create_demo_contacts(db: Session, agents: list[Agent], properties: list[Property]) -> list[Contact]:
    """Create demo contacts for properties."""
    contacts = []

    contact_templates = [
        {
            "property_id": properties[0].id,
            "name": "John Smith",
            "email": "john.smith@example.com",
            "phone": "+13055559876",
            "role": ContactRole.BUYER,
        },
        {
            "property_id": properties[1].id,
            "name": "Mary Johnson",
            "email": "mary.j@example.com",
            "phone": "+13055554321",
            "role": ContactRole.SELLER,
        },
        {
            "property_id": properties[5].id,
            "name": "Robert Davis",
            "email": "rdavis@example.com",
            "phone": "+12125551111",
            "role": ContactRole.BUYER,
        },
        {
            "property_id": properties[10].id,
            "name": "Amanda White",
            "email": "amanda.w@example.com",
            "phone": "+15125552222",
            "role": ContactRole.TENANT,
        },
    ]

    for data in contact_templates:
        contact = Contact(**data)
        db.add(contact)
        contacts.append(contact)

    db.commit()

    print(f"✓ Created {len(contacts)} demo contacts")
    return contacts


def create_demo_analytics_events(db: Session, properties: list[Property], days: int = 30) -> list[AnalyticsEvent]:
    """Generate analytics events for the past N days."""
    events = []
    now = datetime.now(timezone.utc)

    event_types = ["page_view", "inquiry", "showing", "offer", "view_photo"]

    for property in properties:
        # Generate 5-20 events per property
        num_events = randint(5, 20)

        for _ in range(num_events):
            days_ago = randint(0, days)
            event_time = now - timedelta(days=days_ago, hours=randint(0, 23))

            event = AnalyticsEvent(
                property_id=property.id,
                agent_id=property.agent_id,
                event_type=choice(event_types),
                event_name=f"{choice(event_types)}_{property.id}",
                properties={
                    "source": choice(["website", "zillow", "redfin", "referral"]),
                    "session_id": f"session_{randint(1000, 9999)}",
                },
                created_at=event_time,
            )
            events.append(event)

    db.bulk_save_objects(events)
    db.commit()

    print(f"✓ Generated {len(events)} analytics events over {days} days")
    return events


def create_demo_contracts(db: Session, properties: list[Property]) -> list[Contract]:
    """Create demo contracts for properties."""
    contracts = []

    contract_templates = [
        {
            "property_id": properties[0].id,
            "name": "Purchase Agreement - 123 Ocean Drive",
            "status": ContractStatus.SENT,
            "description": "Standard Florida purchase agreement",
        },
        {
            "property_id": properties[3].id,
            "name": "Seller Disclosure - Coral Gables Estate",
            "status": ContractStatus.DRAFT,
            "description": "Florida seller property disclosure",
        },
        {
            "property_id": properties[5].id,
            "name": "Offer Acceptance - Manhattan Penthouse",
            "status": ContractStatus.IN_PROGRESS,
            "description": "Offer accepted by seller",
        },
    ]

    for template in contract_templates:
        contract = Contract(**template)
        db.add(contract)
        contracts.append(contract)

    db.commit()

    print(f"✓ Created {len(contracts)} demo contracts")
    return contracts


def create_demo_alerts(db: Session, agents: list[Agent]) -> list[AnalyticsAlertRule]:
    """Create demo analytics alert rules."""
    alerts = []
    now = datetime.now(timezone.utc)

    alert_templates = [
        {
            "agent_id": agents[0].id,
            "name": "Traffic Drop Alert",
            "description": "Alert when property views drop by 50%",
            "alert_type": AlertType.traffic_drop,
            "metric_name": "property_views",
            "operator": AlertOperator.percentage_drop,
            "threshold_value": 50,
            "time_window_minutes": 60,
            "notification_channels": ["email"],
            "notification_recipients": {"email": ["sarah.johnson@miami-realtor.com"]},
            "severity": "high",
            "enabled": True,
            "created_at": now,
        },
        {
            "agent_id": agents[1].id,
            "name": "Conversion Rate Alert",
            "description": "Alert when conversion rate falls below 2%",
            "alert_type": AlertType.conversion_drop,
            "metric_name": "conversion_rate",
            "operator": AlertOperator.less_than,
            "threshold_value": 2.0,
            "time_window_minutes": 1440,
            "notification_channels": ["email", "slack"],
            "notification_recipients": {
                "email": ["michael.chen@nyluxury.com"],
                "slack": ["https://hooks.slack.com/services/XXX"]
            },
            "severity": "medium",
            "enabled": True,
            "created_at": now,
        },
        {
            "agent_id": agents[2].id,
            "name": "Daily Traffic Summary",
            "description": "Daily summary of property views",
            "alert_type": AlertType.daily_summary,
            "metric_name": "property_views",
            "operator": AlertOperator.greater_than,
            "threshold_value": 0,
            "time_window_minutes": 1440,
            "notification_channels": ["email"],
            "notification_recipients": {"email": ["emily.rodriguez@austinhomes.com"]},
            "severity": "low",
            "enabled": True,
            "created_at": now,
        },
        {
            "agent_id": agents[0].id,
            "name": "High Traffic Alert",
            "description": "Alert when property views exceed 100",
            "alert_type": AlertType.traffic_spike,
            "metric_name": "property_views",
            "operator": AlertOperator.greater_than,
            "threshold_value": 100,
            "time_window_minutes": 60,
            "notification_channels": ["email"],
            "notification_recipients": {"email": ["sarah.johnson@miami-realtor.com"]},
            "severity": "medium",
            "enabled": True,
            "created_at": now,
        },
    ]

    for template in alert_templates:
        alert = AnalyticsAlertRule(**template)
        db.add(alert)
        alerts.append(alert)

    db.commit()

    print(f"✓ Created {len(alerts)} demo alert rules")
    return alerts


def create_demo_notifications(db: Session, agents: list[Agent], properties: list[Property]) -> list[Notification]:
    """Create demo notifications."""
    notifications = []

    notification_templates = [
        {
            "agent_id": agents[0].id,
            "type": NotificationType.GENERAL,
            "priority": NotificationPriority.HIGH,
            "title": "Traffic Drop Detected",
            "message": "Property views for 123 Ocean Drive dropped by 52% in the last hour.",
            "property_id": properties[0].id,
        },
        {
            "agent_id": agents[0].id,
            "type": NotificationType.DAILY_DIGEST,
            "priority": NotificationPriority.MEDIUM,
            "title": "Daily Property Report Ready",
            "message": "Your daily analytics report for 5 active properties is ready.",
        },
        {
            "agent_id": agents[0].id,
            "type": NotificationType.FOLLOW_UP_DUE,
            "priority": NotificationPriority.HIGH,
            "title": "Follow Up: 123 Ocean Drive",
            "message": "Buyer John Smith requested a follow-up call regarding the Miami Beach condo.",
            "property_id": properties[0].id,
        },
        {
            "agent_id": agents[1].id,
            "type": NotificationType.CONTRACT_DEADLINE,
            "priority": NotificationPriority.URGENT,
            "title": "Contract Deadline: 245 Park Avenue",
            "message": "Purchase agreement for 245 Park Avenue expires in 48 hours.",
        },
        {
            "agent_id": agents[2].id,
            "type": NotificationType.NEW_LEAD,
            "priority": NotificationPriority.LOW,
            "title": "New Lead Received",
            "message": "New lead from Austin Open House: David Lee (512) 555-5678.",
        },
    ]

    for data in notification_templates:
        notification = Notification(**data)
        db.add(notification)
        notifications.append(notification)

    db.commit()

    print(f"✓ Created {len(notifications)} demo notifications")
    return notifications


def main():
    """Seed the demo database."""
    import argparse

    parser = argparse.ArgumentParser(description="Seed demo database")
    parser.add_argument("--force", action="store_true", help="Force re-seed even if data exists")
    args = parser.parse_args()

    print("=" * 60)
    print("🌱 SEEDING DEMO DATABASE")
    print("=" * 60)
    print()

    db = SessionLocal()
    try:
        print("1. Setting up agents...")
        agents = create_demo_agents(db)

        print("2. Creating demo properties...")
        properties = create_demo_properties(db, agents)

        print("3. Creating demo contacts...")
        contacts = create_demo_contacts(db, agents, properties)

        print("4. Generating analytics events (30 days)...")
        events = create_demo_analytics_events(db, properties, days=30)

        print("5. Creating demo contracts...")
        contracts = create_demo_contracts(db, properties)

        print("6. Creating demo alerts...")
        alerts = create_demo_alerts(db, agents)

        print("7. Creating demo notifications...")
        notifications = create_demo_notifications(db, agents, properties)

        print()
        print("=" * 60)
        print("✅ DEMO DATABASE SEEDING COMPLETE")
        print("=" * 60)
        print()
        print("Summary:")
        print(f"  • {len(agents)} agents across 3 cities")
        print(f"  • {len(properties)} properties (prices: ${min(p.price for p in properties):,} - ${max(p.price for p in properties):,})")
        print(f"  • {len(contacts)} contacts")
        print(f"  • {len(events)} analytics events")
        print(f"  • {len(contracts)} contracts")
        print(f"  • {len(alerts)} alert rules")
        print(f"  • {len(notifications)} notifications")
        print()
        print("🎉 Your demo database is ready for testing!")
        print()
        print("Test URLs:")
        print(f"  • http://localhost:8000/docs")
        print(f"  • http://localhost:8000/analytics/alerts/rules")
        print(f"  • http://localhost:8000/properties")
        print()

    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
