"""Skills System API router.

Provides endpoints for managing agent skills and capabilities.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.database import get_db
from app.services.skills import skills_service
from app.models.skill import Skill, AgentSkill, SkillReview


router = APIRouter(prefix="/skills", tags=["Skills System"])


# Pydantic models
class SkillInstallRequest(BaseModel):
    """Request to install a skill."""
    skill_name: str
    config: Dict[str, Any] = Field(default_factory=dict)


class SkillRateRequest(BaseModel):
    """Request to rate a skill."""
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    review: Optional[str] = Field(None, description="Optional review text")


class SkillCreateRequest(BaseModel):
    """Request to create a custom skill."""
    name: str
    description: str
    instructions: str
    category: str = "general"
    tags: List[str] = Field(default_factory=list)
    allowed_tools: List[str] = Field(default_factory=list)
    code: Optional[str] = None


@router.get("/marketplace")
async def list_marketplace_skills(
    db: Session = Depends(get_db),
    query: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None
):
    """Browse the skills marketplace.

    Filter by search query, category, or tag.
    """
    skills = skills_service.search_skills(
        db,
        query=query,
        category=category,
        tags=[tag] if tag else None
    )

    return {
        "total_skills": len(skills),
        "skills": [
            {
                "id": skill.id,
                "name": skill.name,
                "slug": skill.slug,
                "description": skill.description,
                "category": skill.category,
                "tags": skill.tags,
                "version": skill.version,
                "author": skill.author_name,
                "license": skill.license,
                "installation_count": skill.installation_count,
                "average_rating": skill.average_rating,
                "rating_count": skill.rating_count,
                "is_verified": skill.is_verified,
                "is_featured": skill.is_featured
            }
            for skill in skills
        ]
    }


@router.get("/installed/{agent_id}")
async def list_installed_skills(
    agent_id: int,
    db: Session = Depends(get_db),
    enabled_only: bool = True
):
    """List skills installed for an agent."""
    skills = skills_service.get_agent_skills(db, agent_id, enabled_only=enabled_only)

    return {
        "agent_id": agent_id,
        "total_skills": len(skills),
        "skills": [
            {
                "id": skill.id,
                "name": skill.name,
                "description": skill.description,
                "category": skill.category,
                "version": skill.version,
                "installed_at": None  # TODO: Add from AgentSkill
            }
            for skill in skills
        ]
    }


@router.post("/install")
async def install_skill(
    request: SkillInstallRequest,
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Install a skill for an agent."""
    try:
        agent_skill = skills_service.install_skill(
            db,
            agent_id=agent_id,
            skill_name=request.skill_name,
            config=request.config
        )

        skill = db.query(Skill).filter(Skill.id == agent_skill.skill_id).first()

        return {
            "status": "installed",
            "skill": {
                "id": skill.id,
                "name": skill.name,
                "description": skill.description
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/uninstall/{skill_name}")
async def uninstall_skill(
    skill_name: str,
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Uninstall a skill for an agent."""
    success = skills_service.uninstall_skill(db, agent_id, skill_name)

    if not success:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_name}")

    return {
        "status": "uninstalled",
        "skill_name": skill_name
    }


@router.get("/instructions/{agent_id}")
async def get_skill_instructions(
    agent_id: int,
    db: Session = Depends(get_db),
    skill_name: Optional[str] = None
):
    """Get instructions for agent's installed skills.

    Returns combined markdown with all skill instructions.
    """
    instructions = skills_service.get_skill_instructions(db, agent_id, skill_name)

    return {
        "agent_id": agent_id,
        "skill_name": skill_name,
        "instructions": instructions
    }


@router.get("/categories")
async def get_skill_categories(db: Session = Depends(get_db)):
    """Get all skill categories."""
    categories = db.query(Skill.category).distinct().all()

    return {
        "categories": [c[0] for c in categories if c[0]]
    }


@router.get("/detail/{skill_name}")
async def get_skill_detail(
    skill_name: str,
    db: Session = Depends(get_db)
):
    """Get detailed information about a skill."""
    skill = db.query(Skill).filter(Skill.name == skill_name).first()

    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_name}")

    # Get reviews
    reviews = db.query(SkillReview).filter(SkillReview.skill_id == skill.id).limit(10).all()

    return {
        "id": skill.id,
        "name": skill.name,
        "slug": skill.slug,
        "description": skill.description,
        "instructions": skill.instructions,
        "metadata": skill.metadata,
        "version": skill.version,
        "author": skill.author_name,
        "license": skill.license,
        "compatibility": skill.compatibility,
        "allowed_tools": skill.allowed_tools,
        "category": skill.category,
        "tags": skill.tags,
        "installation_count": skill.installation_count,
        "average_rating": skill.average_rating,
        "rating_count": skill.rating_count,
        "is_verified": skill.is_verified,
        "is_featured": skill.is_featured,
        "github_repo": skill.github_repo,
        "created_at": skill.created_at.isoformat(),
        "updated_at": skill.updated_at.isoformat(),
        "reviews": [
            {
                "rating": r.rating,
                "review": r.review,
                "created_at": r.created_at.isoformat()
            }
            for r in reviews
        ]
    }


@router.post("/rate/{skill_name}")
async def rate_skill(
    skill_name: str,
    request: SkillRateRequest,
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Rate and review a skill."""
    try:
        review = skills_service.rate_skill(
            db,
            agent_id=agent_id,
            skill_name=skill_name,
            rating=request.rating,
            review=request.review
        )

        return {
            "status": "rated",
            "skill_name": skill_name,
            "rating": request.rating
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create")
async def create_custom_skill(
    request: SkillCreateRequest,
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Create a custom skill.

    Agents can create their own skills for specialized workflows.
    """
    # Check if skill already exists
    existing = db.query(Skill).filter(Skill.name == request.name).first()

    if existing:
        raise HTTPException(status_code=400, detail=f"Skill already exists: {request.name}")

    # Create skill
    skill = Skill(
        name=request.name,
        slug=request.name.lower().replace(" ", "-"),
        description=request.description,
        instructions=request.instructions,
        category=request.category,
        tags=request.tags,
        allowed_tools=request.allowed_tools,
        code=request.code,
        is_public=False,  # Custom skills are private by default
        author_id=agent_id
    )

    db.add(skill)
    db.commit()
    db.refresh(skill)

    return {
        "status": "created",
        "skill": {
            "id": skill.id,
            "name": skill.name,
            "slug": skill.slug,
            "description": skill.description
        }
    }


@router.get("/discover")
async def discover_skills():
    """Discover skills from the skills directory.

    Returns skills found in the local skills/ folder.
    """
    skills = skills_service.discover_skills()

    return {
        "total_discovered": len(skills),
        "skills": skills
    }


@router.post("/sync")
async def sync_skills_from_directory(db: Session = Depends(get_db)):
    """Sync skills from the skills directory to the database.

    Imports any new skills found in the skills/ folder.
    """
    discovered_skills = skills_service.discover_skills()

    imported = []

    for skill_data in discovered_skills:
        # Check if already exists
        existing = db.query(Skill).filter(Skill.name == skill_data["name"]).first()

        if not existing:
            # Create new skill
            skill = Skill(
                name=skill_data["name"],
                slug=skill_data["name"].lower().replace(" ", "-"),
                description=skill_data["description"],
                metadata=skill_data["metadata"],
                instructions=skill_data["instructions"],
                version=skill_data.get("version", "1.0.0"),
                author_name=skill_data.get("author_name"),
                license=skill_data.get("license", "MIT"),
                compatibility=skill_data.get("compatibility", {}),
                allowed_tools=skill_data.get("allowed_tools", []),
                category=skill_data.get("category", "general"),
                tags=skill_data.get("tags", []),
                code=skill_data.get("code"),
                is_public=True
            )

            db.add(skill)
            imported.append(skill_data["name"])

    db.commit()

    return {
        "status": "synced",
        "total_discovered": len(discovered_skills),
        "imported": imported,
        "skipped": len(discovered_skills) - len(imported)
    }
