"""Deal Outcome tracking for learning system."""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.sql import func
import enum

from app.database import Base


class OutcomeStatus(str, enum.Enum):
    """Final outcome of a deal."""
    CLOSED_WON = "closed_won"  # Successfully closed
    CLOSED_LOST = "closed_lost"  # Deal fell through
    WITHDRAWN = "withdrawn"  # Agent withdrew
    STALLED = "stalled"  # No activity > 30 days
    ACTIVE = "active"  # Still in progress


class DealOutcome(Base):
    """Track actual deal outcomes for machine learning."""
    __tablename__ = "deal_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    # Outcome tracking
    status = Column(Enum(OutcomeStatus), default=OutcomeStatus.ACTIVE)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    days_to_close = Column(Integer, nullable=True)

    # Financials (actual vs predicted)
    final_sale_price = Column(Float, nullable=True)
    original_list_price = Column(Float, nullable=True)
    price_reduction_count = Column(Integer, default=0)

    # Prediction snapshot (what we predicted when)
    predicted_probability = Column(Float, nullable=True)
    predicted_days_to_close = Column(Integer, nullable=True)
    prediction_confidence = Column(String(20), nullable=True)

    # Feature snapshot (what we knew when)
    feature_snapshot = Column(JSON, nullable=True)

    # Outcome metadata
    outcome_reason = Column(String, nullable=True)  # Why did it succeed/fail?
    lessons_learned = Column(String, nullable=True)  # Free-form insights

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AgentPerformanceMetrics(Base):
    """Track agent performance patterns for learning."""
    __tablename__ = "agent_performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    # Period tracking (week, month, quarter, year)
    period_type = Column(String(10), nullable=False)  # 'week', 'month', 'quarter', 'year'
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Deal metrics
    total_deals = Column(Integer, default=0)
    closed_deals = Column(Integer, default=0)
    closed_won = Column(Integer, default=0)
    closing_rate = Column(Float, default=0.0)

    # Financial metrics
    total_volume = Column(Float, default=0.0)
    average_deal_size = Column(Float, default=0.0)
    total_profit = Column(Float, default=0.0)

    # Efficiency metrics
    average_days_to_close = Column(Float, nullable=True)
    average_deal_score = Column(Float, nullable=True)

    # Best performers
    best_property_types = Column(JSON, nullable=True)  # [{"type": "condo", "close_rate": 0.8}]
    best_cities = Column(JSON, nullable=True)
    best_price_ranges = Column(JSON, nullable=True)

    # Pattern insights
    success_patterns = Column(JSON, nullable=True)  # AI-generated insights
    failure_patterns = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PredictionLog(Base):
    """Log every prediction for model evaluation."""
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)

    # Prediction details
    predicted_probability = Column(Float, nullable=False)
    predicted_days = Column(Integer, nullable=False)
    confidence = Column(String(20), nullable=False)

    # Features used
    deal_score = Column(Float, nullable=True)
    completion_rate = Column(Float, nullable=True)
    has_contacts = Column(Integer, default=0)
    has_skip_trace = Column(Integer, default=0)
    activity_velocity = Column(Float, nullable=True)

    # Full feature snapshot
    feature_snapshot = Column(JSON, nullable=True)

    # Actual outcome (filled in later)
    actual_outcome = Column(Enum(OutcomeStatus), nullable=True)
    actual_days_to_close = Column(Integer, nullable=True)

    # Accuracy metrics
    probability_error = Column(Float, nullable=True)  # predicted - actual
    was_correct_direction = Column(Integer, nullable=True)  # 1 if predicted > 0.5 and outcome = closed_won

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    outcome_recorded_at = Column(DateTime(timezone=True), nullable=True)
