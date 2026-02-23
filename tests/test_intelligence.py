"""Integration tests for AI Intelligence Layer."""

import pytest
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app.database import SessionLocal, Base, engine
from app.models import (
    Property, Agent, PropertyStatus, PropertyType,
    DealOutcome, OutcomeStatus, AgentPerformanceMetrics, PredictionLog
)
from app.services.predictive_intelligence_service import predictive_intelligence_service
from app.services.learning_system_service import learning_system_service
from app.services.market_opportunity_scanner import market_opportunity_scanner
from app.services.relationship_intelligence_service import relationship_intelligence_service
from app.services.negotiation_agent_service import negotiation_agent_service
from app.services.document_analyzer_service import document_analyzer_service
from app.services.competitive_intelligence_service import competitive_intelligence_service
from app.services.deal_sequencer_service import deal_sequencer_service


class TestPredictiveIntelligence:
    """Test predictive intelligence service."""

    def test_predict_property_outcome(self, db_session):
        """Test closing probability prediction."""
        # Create test property
        agent = db_session.query(Agent).first()
        if not agent:
            pytest.skip("No agent found")

        prop = Property(
            title="Test Property",
            address="123 Test St",
            city="Miami",
            state="FL",
            zip_code="33101",
            price=450000,
            property_type=PropertyType.HOUSE,
            agent_id=agent.id,
            deal_score=75,
            score_grade="B"
        )
        db_session.add(prop)
        db_session.commit()

        # Test prediction
        result = predictive_intelligence_service.predict_property_outcome(db_session, prop.id)

        assert "error" not in result
        assert "closing_probability" in result
        assert 0 <= result["closing_probability"] <= 1
        assert "confidence" in result
        assert "risk_factors" in result
        assert "strengths" in result
        assert "voice_summary" in result

    def test_recommend_next_action(self, db_session):
        """Test action recommendation."""
        prop = db_session.query(Property).first()
        if not prop:
            pytest.skip("No property found")

        result = predictive_intelligence_service.recommend_next_action(db_session, prop.id)

        assert "error" not in result
        assert "recommended_action" in result
        assert "reasoning" in result
        assert "priority" in result


class TestLearningSystem:
    """Test adaptive learning system."""

    def test_record_outcome(self, db_session):
        """Test recording deal outcomes."""
        prop = db_session.query(Property).first()
        if not prop:
            pytest.skip("No property found")

        # Record outcome
        result = learning_system_service.record_outcome(
            db_session,
            property_id=prop.id,
            status=OutcomeStatus.CLOSED_WON,
            final_sale_price=450000,
            outcome_reason="Great deal",
            lessons_learned="Move faster on high-score properties"
        )

        assert "error" not in result
        assert result["status"] == OutcomeStatus.CLOSED_WON.value

        # Verify it was saved
        outcome = db_session.query(DealOutcome).filter(
            DealOutcome.property_id == prop.id
        ).first()
        assert outcome is not None
        assert outcome.status == OutcomeStatus.CLOSED_WON

    def test_get_agent_patterns(self, db_session):
        """Test pattern discovery."""
        agent = db_session.query(Agent).first()
        if not agent:
            pytest.skip("No agent found")

        result = learning_system_service.get_agent_success_patterns(
            db_session, agent.id, period="month"
        )

        # Should not error, even with no data
        assert "agent_id" in result
        assert "period" in result


class TestMarketOpportunities:
    """Test market opportunity scanner."""

    def test_scan_opportunities(self, db_session):
        """Test opportunity scanning."""
        agent = db_session.query(Agent).first()
        if not agent:
            pytest.skip("No agent found")

        result = market_opportunity_scanner.scan_market_opportunities(
            db_session, agent_id=agent.id, limit=5, min_score=70
        )

        assert "agent_id" in result
        assert "total_scanned" in result
        assert "opportunities" in result


class TestRelationshipIntelligence:
    """Test relationship intelligence service."""

    def test_score_relationship_health(self, db_session):
        """Test relationship health scoring."""
        from app.models import Contact

        contact = db_session.query(Contact).first()
        if not contact:
            pytest.skip("No contact found")

        result = relationship_intelligence_service.score_relationship_health(
            db_session, contact.id
        )

        assert "error" not in result
        assert "health_score" in result
        assert 0 <= result["health_score"] <= 100
        assert "trend" in result


class TestNegotiationAgent:
    """Test negotiation agent service."""

    def test_analyze_offer(self, db_session):
        """Test offer analysis."""
        prop = db_session.query(Property).first()
        if not prop or not prop.price:
            pytest.skip("No property with price found")

        result = negotiation_agent_service.analyze_offer(
            db_session, prop.id, offer_amount=prop.price * 0.95
        )

        assert "error" not in result
        assert "acceptance_probability" in result
        assert "recommendation" in result
        assert "walkaway_price" in result


class TestDocumentAnalyzer:
    """Test document analyzer service."""

    def test_analyze_inspection_report(self, db_session):
        """Test inspection report analysis."""
        prop = db_session.query(Property).first()
        if not prop:
            pytest.skip("No property found")

        # Sample inspection report text
        inspection_text = """
        INSPECTION REPORT
        Property: 123 Test St

        EXTERIOR:
        Roof: Good condition, minor wear
        Foundation: No issues detected

        ELECTRICAL:
        Panel: Updated, in good condition
        Outlets: All functioning properly

        PLUMBING:
        Pipes: No leaks detected
        Water heater: 5 years old, functioning well

        HVAC:
        System: Working properly, serviced recently
        """

        result = document_analyzer_service.analyze_inspection_report(
            db_session, prop.id, inspection_text, create_note=False
        )

        assert "error" not in result
        assert "critical_issues" in result
        assert "total_repair_estimate" in result


class TestCompetitiveIntelligence:
    """Test competitive intelligence service."""

    def test_analyze_market_competition(self, db_session):
        """Test market competition analysis."""
        # Create some test data
        result = competitive_intelligence_service.analyze_market_competition(
            db_session, city="Miami", state="FL", days_back=90
        )

        # Should not error
        assert "city" in result
        assert "state" in result


class TestDealSequencer:
    """Test deal sequencer service."""

    def test_sequence_sell_and_buy(self, db_session):
        """Test sell-and-buy sequencing."""
        props = db_session.query(Property).limit(2).all()
        if len(props) < 2:
            pytest.skip("Need at least 2 properties")

        result = deal_sequencer_service.sequence_sell_and_buy(
            db_session,
            sale_property_id=props[0].id,
            purchase_property_id=props[1].id,
            contingency_type="sale_contingent"
        )

        assert "error" not in result
        assert "sequence" in result


# Fixtures
@pytest.fixture
def db_session():
    """Create test database session."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


if __name__ == "__main__":
    # Run tests manually
    print("Running intelligence layer tests...")
    pytest.main([__file__, "-v"])
