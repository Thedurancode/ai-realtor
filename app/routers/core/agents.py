from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.agent import Agent
from app.auth import generate_api_key, hash_api_key
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse, AgentRegister, AgentRegisterResponse

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/register", response_model=AgentRegisterResponse, status_code=201)
def register_agent(agent: AgentRegister, db: Session = Depends(get_db)):
    """Public registration endpoint. Creates an agent and returns an API key."""
    existing = db.query(Agent).filter(Agent.email == agent.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    api_key = generate_api_key()
    new_agent = Agent(
        name=agent.name,
        email=agent.email,
        phone=agent.phone or None,
        license_number=agent.license_number or None,
        api_key_hash=hash_api_key(api_key),
    )
    db.add(new_agent)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="License number already in use")
    db.refresh(new_agent)

    return AgentRegisterResponse(
        id=new_agent.id,
        name=new_agent.name,
        email=new_agent.email,
        api_key=api_key,
        created_at=new_agent.created_at,
    )


@router.post("/", response_model=AgentResponse, status_code=201)
def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    db_agent = db.query(Agent).filter(Agent.email == agent.email).first()
    if db_agent:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_agent = Agent(**agent.model_dump())
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    return new_agent


@router.get("/", response_model=list[AgentResponse])
def list_agents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    agents = db.query(Agent).offset(skip).limit(limit).all()
    return agents


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.patch("/{agent_id}", response_model=AgentResponse)
def update_agent(agent_id: int, agent: AgentUpdate, db: Session = Depends(get_db)):
    db_agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    update_data = agent.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_agent, field, value)

    db.commit()
    db.refresh(db_agent)
    return db_agent


@router.delete("/{agent_id}", status_code=204)
def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    db_agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    db.delete(db_agent)
    db.commit()
    return None
