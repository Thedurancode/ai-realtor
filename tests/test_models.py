"""Tests for SQLAlchemy models and Pydantic schemas."""

from datetime import datetime, date

from app.models.property import Property, PropertyStatus, PropertyType, DealType
from app.models.contact import Contact, ContactRole
from app.models.contract import Contract, ContractStatus, RequirementSource
from app.models.todo import Todo, TodoStatus, TodoPriority
from app.models.offer import Offer, OfferStatus, FinancingType
from app.models.agent import Agent
from app.models.notification import Notification, NotificationType, NotificationPriority


# ---- Enum Tests ----

class TestPropertyEnums:
    def test_property_status_values(self):
        assert PropertyStatus.NEW_PROPERTY.value == "new_property"
        assert PropertyStatus.ENRICHED.value == "enriched"
        assert PropertyStatus.RESEARCHED.value == "researched"
        assert PropertyStatus.WAITING_FOR_CONTRACTS.value == "waiting_for_contracts"
        assert PropertyStatus.COMPLETE.value == "complete"

    def test_property_type_values(self):
        assert PropertyType.HOUSE.value == "HOUSE"
        assert PropertyType.CONDO.value == "CONDO"
        assert PropertyType.LAND.value == "LAND"
        assert PropertyType.COMMERCIAL.value == "COMMERCIAL"

    def test_deal_type_values(self):
        assert DealType.TRADITIONAL.value == "TRADITIONAL"
        assert DealType.SHORT_SALE.value == "SHORT_SALE"
        assert DealType.WHOLESALE.value == "WHOLESALE"
        assert DealType.RENTAL.value == "RENTAL"


class TestContactEnums:
    def test_all_roles(self):
        expected_roles = [
            "lawyer", "attorney", "contractor", "inspector", "appraiser",
            "mortgage_broker", "lender", "title_company", "buyer", "seller",
            "tenant", "landlord", "property_manager", "handyman", "plumber",
            "electrician", "photographer", "stager", "other",
        ]
        actual_roles = [r.value for r in ContactRole]
        for role in expected_roles:
            assert role in actual_roles, f"Missing role: {role}"


class TestContractEnums:
    def test_contract_statuses(self):
        assert ContractStatus.DRAFT.value == "draft"
        assert ContractStatus.SENT.value == "sent"
        assert ContractStatus.COMPLETED.value == "completed"
        assert ContractStatus.CANCELLED.value == "cancelled"

    def test_requirement_sources(self):
        assert RequirementSource.AUTO_ATTACHED.value == "auto_attached"
        assert RequirementSource.MANUAL.value == "manual"
        assert RequirementSource.AI_SUGGESTED.value == "ai_suggested"


class TestTodoEnums:
    def test_todo_statuses(self):
        assert TodoStatus.PENDING.value == "pending"
        assert TodoStatus.IN_PROGRESS.value == "in_progress"
        assert TodoStatus.COMPLETED.value == "completed"
        assert TodoStatus.CANCELLED.value == "cancelled"

    def test_todo_priorities(self):
        assert TodoPriority.LOW.value == "low"
        assert TodoPriority.MEDIUM.value == "medium"
        assert TodoPriority.HIGH.value == "high"
        assert TodoPriority.URGENT.value == "urgent"


class TestOfferEnums:
    def test_offer_statuses(self):
        assert OfferStatus.DRAFT.value == "draft"
        assert OfferStatus.SUBMITTED.value == "submitted"
        assert OfferStatus.COUNTERED.value == "countered"
        assert OfferStatus.ACCEPTED.value == "accepted"
        assert OfferStatus.REJECTED.value == "rejected"
        assert OfferStatus.WITHDRAWN.value == "withdrawn"

    def test_financing_types(self):
        assert FinancingType.CASH.value == "cash"
        assert FinancingType.CONVENTIONAL.value == "conventional"
        assert FinancingType.FHA.value == "fha"
        assert FinancingType.HARD_MONEY.value == "hard_money"


# ---- Model Creation Tests ----

class TestAgentModel:
    def test_create_agent(self, db):
        a = Agent(name="Model Test", email="model@test.com")
        db.add(a)
        db.commit()
        db.refresh(a)
        assert a.id is not None
        assert a.created_at is not None

    def test_agent_unique_email(self, db):
        import pytest
        from sqlalchemy.exc import IntegrityError
        a1 = Agent(name="A1", email="unique@test.com")
        db.add(a1)
        db.commit()
        a2 = Agent(name="A2", email="unique@test.com")
        db.add(a2)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


class TestPropertyModel:
    def test_create_property(self, db, agent):
        p = Property(
            title="Model Test Property",
            address="1 Test Ave",
            city="TestCity",
            state="NJ",
            zip_code="07000",
            price=100000,
            agent_id=agent.id,
        )
        db.add(p)
        db.commit()
        db.refresh(p)
        assert p.id is not None
        assert p.status == PropertyStatus.NEW_PROPERTY
        assert p.property_type == PropertyType.HOUSE

    def test_property_relationships(self, db, sample_property):
        assert sample_property.agent is not None
        assert sample_property.agent.name == "Test Agent"


class TestContactModel:
    def test_create_contact(self, db, sample_property):
        c = Contact(
            property_id=sample_property.id,
            name="Test Contact",
            role=ContactRole.BUYER,
        )
        db.add(c)
        db.commit()
        db.refresh(c)
        assert c.id is not None
        assert c.role == ContactRole.BUYER

    def test_contact_relationship(self, db, sample_contact):
        assert sample_contact.property is not None


class TestContractModel:
    def test_create_contract(self, db, sample_property):
        c = Contract(
            property_id=sample_property.id,
            name="Test Contract",
            status=ContractStatus.DRAFT,
        )
        db.add(c)
        db.commit()
        db.refresh(c)
        assert c.id is not None
        assert c.is_required is True
        assert c.requirement_source == RequirementSource.AUTO_ATTACHED


class TestTodoModel:
    def test_create_todo(self, db, sample_property):
        t = Todo(
            property_id=sample_property.id,
            title="Test Todo",
        )
        db.add(t)
        db.commit()
        db.refresh(t)
        assert t.id is not None
        assert t.status == TodoStatus.PENDING
        assert t.priority == TodoPriority.MEDIUM


class TestOfferModel:
    def test_create_offer(self, db, sample_property):
        o = Offer(
            property_id=sample_property.id,
            offer_price=200000,
            financing_type=FinancingType.CASH,
            status=OfferStatus.DRAFT,
        )
        db.add(o)
        db.commit()
        db.refresh(o)
        assert o.id is not None
        assert o.is_our_offer is True

    def test_offer_counter_relationship(self, db, sample_property):
        parent = Offer(
            property_id=sample_property.id,
            offer_price=200000,
            status=OfferStatus.SUBMITTED,
        )
        db.add(parent)
        db.commit()

        counter = Offer(
            property_id=sample_property.id,
            offer_price=220000,
            parent_offer_id=parent.id,
            status=OfferStatus.SUBMITTED,
        )
        db.add(counter)
        db.commit()
        db.refresh(counter)

        assert counter.parent_offer_id == parent.id


# ---- Schema Tests ----

class TestPropertySchemas:
    def test_property_create_schema(self):
        from app.schemas.property import PropertyCreate
        schema = PropertyCreate(
            title="Schema Test",
            address="1 Schema St",
            city="Test",
            state="NJ",
            zip_code="07000",
            price=100000,
            agent_id=1,
        )
        assert schema.title == "Schema Test"
        assert schema.status == PropertyStatus.NEW_PROPERTY

    def test_property_update_schema(self):
        from app.schemas.property import PropertyUpdate
        schema = PropertyUpdate(price=200000)
        dumped = schema.model_dump(exclude_unset=True)
        assert dumped == {"price": 200000}
        assert "title" not in dumped


class TestAgentSchemas:
    def test_agent_create_schema(self):
        from app.schemas.agent import AgentCreate
        schema = AgentCreate(
            email="schema@test.com",
            name="Schema Agent",
        )
        assert schema.email == "schema@test.com"

    def test_agent_register_schema(self):
        from app.schemas.agent import AgentRegister
        schema = AgentRegister(
            email="reg@test.com",
            name="Register Agent",
        )
        assert schema.phone is None

    def test_agent_update_partial(self):
        from app.schemas.agent import AgentUpdate
        schema = AgentUpdate(name="New Name")
        dumped = schema.model_dump(exclude_unset=True)
        assert dumped == {"name": "New Name"}


class TestContactSchemas:
    def test_contact_create_schema(self):
        from app.schemas.contact import ContactCreate
        schema = ContactCreate(
            property_id=1,
            name="Test",
            role=ContactRole.BUYER,
        )
        assert schema.property_id == 1

    def test_contact_voice_schema(self):
        from app.schemas.contact import ContactCreateFromVoice
        schema = ContactCreateFromVoice(
            address_query="123 main",
            role="lawyer",
            name="John Doe",
            phone="555-1234",
        )
        assert schema.session_id == "default"


class TestOfferSchemas:
    def test_offer_create_schema(self):
        from app.schemas.offer import OfferCreate
        schema = OfferCreate(
            property_id=1,
            offer_price=250000,
        )
        assert schema.financing_type == "cash"
        assert schema.closing_days == 30
        assert schema.contingencies == []
        assert schema.expires_in_hours == 48

    def test_counter_offer_schema(self):
        from app.schemas.offer import CounterOfferCreate
        schema = CounterOfferCreate(offer_price=260000)
        assert schema.closing_days is None

    def test_format_currency(self):
        from app.schemas.offer import format_currency
        assert format_currency(250000) == "$250,000"
        assert format_currency(None) == "N/A"
        assert format_currency(1234567.89) == "$1,234,568"

    def test_format_datetime(self):
        from app.schemas.offer import format_datetime
        dt = datetime(2026, 3, 15, 14, 30)
        result = format_datetime(dt)
        assert "Mar" in result
        assert "15" in result
        assert format_datetime(None) is None
