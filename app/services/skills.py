"""Skills System Service.

Manages skill packages that extend agent capabilities.
Inspired by skills.sh and ZeroClaw's skills system.
"""

import os
import re
import json
import yaml
import toml
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from pathlib import Path

from app.models.skill import Skill, AgentSkill, SkillReview
from app.models.agent import Agent


class SkillsService:
    """Service for managing agent skills."""

    def __init__(self, skills_dir: str = "skills"):
        """Initialize skills service.

        Args:
            skills_dir: Directory containing skill packages
        """
        self.skills_dir = Path(skills_dir)
        self.skills_dir.mkdir(exist_ok=True)

    def discover_skills(self) -> List[Dict[str, Any]]:
        """Discover all skill packages in the skills directory.

        Returns:
            List of skill metadata dictionaries
        """
        skills = []

        for skill_path in self.skills_dir.iterdir():
            if not skill_path.is_dir():
                continue

            # Look for SKILL.md or skill.toml
            skill_md = skill_path / "SKILL.md"
            skill_toml = skill_path / "skill.toml"

            if skill_md.exists():
                skill = self._parse_skill_markdown(skill_md)
            elif skill_toml.exists():
                skill = self._parse_skill_toml(skill_toml)
            else:
                continue

            if skill:
                skills.append(skill)

        return skills

    def _parse_skill_markdown(self, md_path: Path) -> Optional[Dict[str, Any]]:
        """Parse SKILL.md file with YAML frontmatter.

        Args:
            md_path: Path to SKILL.md

        Returns:
            Skill metadata dictionary
        """
        content = md_path.read_text()

        # Extract YAML frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)

        if not frontmatter_match:
            return None

        frontmatter_yaml = frontmatter_match.group(1)
        instructions_markdown = frontmatter_match.group(2)

        try:
            metadata = yaml.safe_load(frontmatter_yaml)
        except yaml.YAMLError:
            return None

        return {
            "name": metadata.get("name"),
            "description": metadata.get("description"),
            "metadata": metadata,
            "instructions": instructions_markdown,
            "version": metadata.get("metadata", {}).get("version", "1.0.0"),
            "author_name": metadata.get("metadata", {}).get("author"),
            "license": metadata.get("license", "MIT"),
            "compatibility": metadata.get("compatibility", {}),
            "allowed_tools": metadata.get("metadata", {}).get("allowed-tools", []),
            "category": metadata.get("metadata", {}).get("category", "general"),
            "tags": metadata.get("metadata", {}).get("tags", [])
        }

    def _parse_skill_toml(self, toml_path: Path) -> Optional[Dict[str, Any]]:
        """Parse skill.toml file.

        Args:
            toml_path: Path to skill.toml

        Returns:
            Skill metadata dictionary
        """
        try:
            data = toml.load(toml_path)
        except toml.TomlDecodeError:
            return None

        # Load instructions from separate markdown file if specified
        instructions = ""
        if "instructions_file" in data:
            instructions_path = toml_path.parent / data["instructions_file"]
            if instructions_path.exists():
                instructions = instructions_path.read_text()

        return {
            "name": data.get("name"),
            "description": data.get("description"),
            "metadata": data,
            "instructions": instructions or data.get("instructions", ""),
            "version": data.get("version", "1.0.0"),
            "author_name": data.get("author"),
            "license": data.get("license", "MIT"),
            "compatibility": data.get("compatibility", {}),
            "allowed_tools": data.get("allowed_tools", []),
            "category": data.get("category", "general"),
            "tags": data.get("tags", []),
            "code": data.get("code")
        }

    def install_skill(
        self,
        db: Session,
        agent_id: int,
        skill_name: str,
        config: Optional[Dict] = None
    ) -> AgentSkill:
        """Install a skill for an agent.

        Args:
            db: Database session
            agent_id: Agent ID
            skill_name: Name of skill to install
            config: Optional installation-specific configuration

        Returns:
            AgentSkill instance

        Raises:
            ValueError: If skill not found
        """
        # Find skill
        skill = db.query(Skill).filter(Skill.name == skill_name).first()

        if not skill:
            raise ValueError(f"Skill not found: {skill_name}")

        # Check if already installed
        existing = db.query(AgentSkill).filter(
            AgentSkill.agent_id == agent_id,
            AgentSkill.skill_id == skill.id
        ).first()

        if existing:
            return existing

        # Install skill
        agent_skill = AgentSkill(
            agent_id=agent_id,
            skill_id=skill.id,
            config=config or {}
        )

        db.add(agent_skill)

        # Update installation count
        skill.installation_count += 1

        db.commit()
        db.refresh(agent_skill)

        return agent_skill

    def uninstall_skill(self, db: Session, agent_id: int, skill_name: str) -> bool:
        """Uninstall a skill for an agent.

        Args:
            db: Database session
            agent_id: Agent ID
            skill_name: Name of skill to uninstall

        Returns:
            True if uninstalled, False if not found
        """
        skill = db.query(Skill).filter(Skill.name == skill_name).first()

        if not skill:
            return False

        agent_skill = db.query(AgentSkill).filter(
            AgentSkill.agent_id == agent_id,
            AgentSkill.skill_id == skill.id
        ).first()

        if not agent_skill:
            return False

        db.delete(agent_skill)
        db.commit()

        return True

    def get_agent_skills(
        self,
        db: Session,
        agent_id: int,
        enabled_only: bool = True
    ) -> List[Skill]:
        """Get all skills installed for an agent.

        Args:
            db: Database session
            agent_id: Agent ID
            enabled_only: Only return enabled skills

        Returns:
            List of Skill instances
        """
        query = db.query(Skill).join(AgentSkill).filter(AgentSkill.agent_id == agent_id)

        if enabled_only:
            query = query.filter(AgentSkill.is_enabled == True)

        return query.all()

    def get_skill_instructions(
        self,
        db: Session,
        agent_id: int,
        skill_name: Optional[str] = None
    ) -> str:
        """Get instructions for agent's skills.

        Args:
            db: Database session
            agent_id: Agent ID
            skill_name: Optional specific skill name

        Returns:
            Combined instructions string
        """
        skills = self.get_agent_skills(db, agent_id)

        if skill_name:
            skills = [s for s in skills if s.name == skill_name]

        if not skills:
            return ""

        instructions = []

        for skill in skills:
            instructions.append(f"## Skill: {skill.name}\n")
            instructions.append(f"**Description:** {skill.description}\n\n")
            instructions.append(skill.instructions)
            instructions.append("\n\n---\n\n")

        return "\n".join(instructions)

    def search_skills(
        self,
        db: Session,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Skill]:
        """Search for skills.

        Args:
            db: Database session
            query: Search query (searches name, description, tags)
            category: Filter by category
            tags: Filter by tags (any match)

        Returns:
            List of matching skills
        """
        skills_query = db.query(Skill).filter(Skill.is_public == True)

        if category:
            skills_query = skills_query.filter(Skill.category == category)

        if tags:
            for tag in tags:
                skills_query = skills_query.filter(Skill.tags.contains(tag))

        if query:
            search_filter = f"%{query}%"
            skills_query = skills_query.filter(
                (Skill.name.ilike(search_filter)) |
                (Skill.description.ilike(search_filter)) |
                (Skill.tags.contains(query))
            )

        return skills_query.order_by(Skill.installation_count.desc()).all()

    def rate_skill(
        self,
        db: Session,
        agent_id: int,
        skill_name: str,
        rating: int,
        review: Optional[str] = None
    ) -> SkillReview:
        """Rate and review a skill.

        Args:
            db: Database session
            agent_id: Agent ID
            skill_name: Name of skill
            rating: Rating 1-5
            review: Optional review text

        Returns:
            SkillReview instance

        Raises:
            ValueError: If skill not found or rating invalid
        """
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        skill = db.query(Skill).filter(Skill.name == skill_name).first()

        if not skill:
            raise ValueError(f"Skill not found: {skill_name}")

        # Check for existing review
        existing_review = db.query(SkillReview).filter(
            SkillReview.agent_id == agent_id,
            SkillReview.skill_id == skill.id
        ).first()

        if existing_review:
            # Update existing review
            old_rating = existing_review.rating
            existing_review.rating = rating
            existing_review.review = review

            # Recalculate average
            skill.rating_count = skill.rating_count
            skill.average_rating = int((skill.average_rating * skill.rating_count - old_rating + rating) / skill.rating_count)
        else:
            # Create new review
            skill_review = SkillReview(
                skill_id=skill.id,
                agent_id=agent_id,
                rating=rating,
                review=review
            )
            db.add(skill_review)

            # Update average
            skill.rating_count += 1
            skill.average_rating = int((skill.average_rating * (skill.rating_count - 1) + rating) / skill.rating_count)

        db.commit()
        db.refresh(skill)

        return existing_review if existing_review else skill_review

    def create_skill_from_github(
        self,
        db: Session,
        repo_url: str,
        agent_id: int
    ) -> Skill:
        """Create a skill from a GitHub repository.

        Args:
            db: Database session
            repo_url: GitHub repository URL
            agent_id: Agent ID creating the skill

        Returns:
            Skill instance

        Example:
            skill = skills_service.create_skill_from_github(
                db,
                "https://github.com/owner/repo",
                agent_id=2
            )
        """
        import requests

        # Parse repo URL
        # TODO: Implement GitHub API fetching
        # For now, create placeholder

        skill = Skill(
            name=repo_url.split("/")[-1],
            slug=repo_url.split("/")[-1].lower(),
            description=f"Skill from {repo_url}",
            metadata={"source": "github", "url": repo_url},
            instructions="# Skill from GitHub\n\nInstructions not yet loaded.",
            github_repo=repo_url,
            author_id=agent_id
        )

        db.add(skill)
        db.commit()
        db.refresh(skill)

        return skill


# Global singleton
skills_service = SkillsService()
