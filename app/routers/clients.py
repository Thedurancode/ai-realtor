from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.client import Client
from app.models.property import Property
from app.schemas.client import (
    ClientCreate,
    ClientMatchResponse,
    ClientPreferencesUpdate,
    ClientResponse,
    ClientUpdate,
)

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("/", response_model=ClientResponse, status_code=201)
def create_client(payload: ClientCreate, request: Request, db: Session = Depends(get_db)):
    agent_id = getattr(request.state, "agent_id", 1)
    client = Client(agent_id=agent_id, **payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return ClientResponse.model_validate(client)


@router.get("/", response_model=list[ClientResponse])
def list_clients(
    request: Request,
    client_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    db: Session = Depends(get_db),
):
    agent_id = getattr(request.state, "agent_id", 1)
    q = db.query(Client).filter(Client.agent_id == agent_id)
    if client_type:
        q = q.filter(Client.client_type == client_type)
    if status:
        q = q.filter(Client.status == status)
    if search:
        term = f"%{search}%"
        q = q.filter(
            (Client.first_name.ilike(term))
            | (Client.last_name.ilike(term))
            | (Client.email.ilike(term))
            | (Client.phone.ilike(term))
        )
    q = q.order_by(Client.created_at.desc())
    clients = q.offset(offset).limit(limit).all()
    return [ClientResponse.model_validate(c) for c in clients]


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientResponse.model_validate(client)


@router.patch("/{client_id}", response_model=ClientResponse)
def update_client(client_id: int, payload: ClientUpdate, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(client, key, value)
    db.commit()
    db.refresh(client)
    return ClientResponse.model_validate(client)


@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    db.delete(client)
    db.commit()


@router.post("/{client_id}/preferences", response_model=ClientResponse)
def update_preferences(client_id: int, payload: ClientPreferencesUpdate, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(client, key, value)
    db.commit()
    db.refresh(client)
    return ClientResponse.model_validate(client)


@router.get("/{client_id}/matches", response_model=ClientMatchResponse)
def get_client_matches(client_id: int, request: Request, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    agent_id = getattr(request.state, "agent_id", 1)
    q = db.query(Property).filter(Property.agent_id == agent_id)

    if client.budget_min:
        q = q.filter(Property.price >= client.budget_min)
    if client.budget_max:
        q = q.filter(Property.price <= client.budget_max)
    if client.bedrooms_min:
        q = q.filter(Property.bedrooms >= client.bedrooms_min)
    if client.bathrooms_min:
        q = q.filter(Property.bathrooms >= client.bathrooms_min)
    if client.sqft_min:
        q = q.filter(Property.square_feet >= client.sqft_min)
    if client.preferred_locations:
        q = q.filter(
            (Property.city.in_(client.preferred_locations))
            | (Property.zip_code.in_(client.preferred_locations))
        )

    matches = q.limit(20).all()
    return ClientMatchResponse(
        client=ClientResponse.model_validate(client),
        matching_properties=[
            {
                "id": p.id,
                "address": p.address,
                "city": p.city,
                "state": p.state,
                "price": p.price,
                "bedrooms": p.bedrooms,
                "bathrooms": p.bathrooms,
                "square_feet": p.square_feet,
            }
            for p in matches
        ],
        match_count=len(matches),
    )


@router.get("/{client_id}/activity", response_model=dict)
def get_client_activity(client_id: int, db: Session = Depends(get_db)):
    """Get timeline of interactions with a client."""
    from app.models.showing import Showing
    from app.models.message import Message

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    showings = (
        db.query(Showing)
        .filter(Showing.client_id == client_id)
        .order_by(Showing.scheduled_at.desc())
        .limit(20)
        .all()
    )
    messages = (
        db.query(Message)
        .filter(Message.client_id == client_id)
        .order_by(Message.created_at.desc())
        .limit(20)
        .all()
    )

    return {
        "client_id": client_id,
        "showings": [
            {"id": s.id, "property_id": s.property_id, "scheduled_at": str(s.scheduled_at), "status": s.status.value}
            for s in showings
        ],
        "messages": [
            {"id": m.id, "channel": m.channel.value, "subject": m.subject, "created_at": str(m.created_at)}
            for m in messages
        ],
    }
