from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.message import Message
from app.schemas.message import (
    MessageCreate,
    MessageListResponse,
    MessageResponse,
)

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/", response_model=MessageResponse, status_code=201)
def create_message(payload: MessageCreate, request: Request, db: Session = Depends(get_db)):
    agent_id = getattr(request.state, "agent_id", 1)
    msg = Message(agent_id=agent_id, **payload.model_dump())
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return MessageResponse.model_validate(msg)


@router.get("/client/{client_id}", response_model=MessageListResponse)
def get_client_messages(
    client_id: int,
    channel: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    db: Session = Depends(get_db),
):
    q = db.query(Message).filter(Message.client_id == client_id)
    if channel:
        q = q.filter(Message.channel == channel)
    total = q.count()
    messages = q.order_by(Message.created_at.desc()).offset(offset).limit(limit).all()
    return MessageListResponse(
        messages=[MessageResponse.model_validate(m) for m in messages],
        total=total,
    )


@router.get("/property/{property_id}", response_model=MessageListResponse)
def get_property_messages(
    property_id: int,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    db: Session = Depends(get_db),
):
    q = db.query(Message).filter(Message.property_id == property_id)
    total = q.count()
    messages = q.order_by(Message.created_at.desc()).offset(offset).limit(limit).all()
    return MessageListResponse(
        messages=[MessageResponse.model_validate(m) for m in messages],
        total=total,
    )


@router.post("/send-email", response_model=MessageResponse, status_code=201)
async def send_email(payload: MessageCreate, request: Request, db: Session = Depends(get_db)):
    """Send an email via Resend and log it as a message."""
    if not payload.recipient:
        raise HTTPException(status_code=400, detail="recipient (email address) is required")

    agent_id = getattr(request.state, "agent_id", 1)

    try:
        from app.services.resend_service import resend_service
        await resend_service.send_email(
            to=payload.recipient,
            subject=payload.subject or "No Subject",
            html_body=f"<p>{payload.body}</p>",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Email send failed: {e}")

    msg = Message(
        agent_id=agent_id,
        channel="email",
        direction="outbound",
        **payload.model_dump(exclude={"channel", "direction"}),
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return MessageResponse.model_validate(msg)
