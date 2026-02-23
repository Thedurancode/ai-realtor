"""Skills System Models.

Allows AI agents to learn new capabilities from community TOML + Markdown packs.
Inspired by skills.sh and ZeroClaw's skills system.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Skill(Base):
    """A skill package that extends agent capabilities.

    Skills are reusable capabilities that can be installed per-agent or globally.
    Examples:
    - "luxury-property-negotiation" — Advanced negotiation tactics for luxury properties
    - "short-sale-expert" — Guide agents through short sale process
    - "first-time-home-buyer-coach" — Specialized guidance for first-time buyers
    """

    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)

    # Metadata from SKILL.md frontmatter
    skill_metadata = Column(JSON, default=dict)

    # Skill content (Markdown instructions)
    instructions = Column(Text, nullable=False)

    # Skill code (optional executable scripts)
    code = Column(Text, nullable=True)

    # Skill version
    version = Column(String(20), default="1.0.0")

    # Author information
    author_name = Column(String(100))
    author_email = Column(String(100))

    # License
    license = Column(String(50), default="MIT")

    # Compatibility requirements
    compatibility = Column(JSON, default=dict)

    # Allowed tools (list of MCP tools this skill can use)
    allowed_tools = Column(JSON, default=list)

    # Public/private skill
    is_public = Column(Boolean, default=True)

    # Verified by platform
    is_verified = Column(Boolean, default=False)

    # Featured skill
    is_featured = Column(Boolean, default=False)

    # Category
    category = Column(String(50))
    tags = Column(JSON, default=list)

    # GitHub repo (if from community)
    github_repo = Column(String(200))

    # Installation count
    installation_count = Column(Integer, default=0)

    # Rating
    average_rating = Column(Integer, default=0)
    rating_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    installations = relationship("AgentSkill", back_populates="skill", cascade="all, delete-orphan")
    reviews = relationship("SkillReview", back_populates="skill", cascade="all, delete-orphan")


class AgentSkill(Base):
    """Installation of a skill for a specific agent."""

    __tablename__ = "agent_skills"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)

    # Installation-specific configuration
    config = Column(JSON, default=dict)

    # Enabled/disabled
    is_enabled = Column(Boolean, default=True)

    # Custom notes from agent
    notes = Column(Text)

    # Timestamps
    installed_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    # Relationships
    agent = relationship("Agent", back_populates="installed_skills")
    skill = relationship("Skill", back_populates="installations")


class SkillReview(Base):
    """Reviews and ratings for skills."""

    __tablename__ = "skill_reviews"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    # Rating 1-5
    rating = Column(Integer, nullable=False)

    # Review text
    review = Column(Text)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    skill = relationship("Skill", back_populates="reviews")
    agent = relationship("Agent")
