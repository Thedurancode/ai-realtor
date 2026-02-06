from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class WorkerRun(Base):
    __tablename__ = "worker_runs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("agentic_jobs.id"), nullable=False, index=True)

    worker_name = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False)
    runtime_ms = Column(Integer, nullable=False, default=0)
    cost_usd = Column(Float, nullable=False, default=0.0)
    web_calls = Column(Integer, nullable=False, default=0)

    data = Column(JSON, nullable=True)
    unknowns = Column(JSON, nullable=True)
    errors = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("AgenticJob", back_populates="worker_runs")
