from datetime import datetime

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    client_id: int | None = None
    property_id: int | None = None
    channel: str  # email, sms, phone_call, in_person, note
    direction: str = "outbound"
    subject: str | None = None
    body: str
    recipient: str | None = None


class MessageResponse(BaseModel):
    id: int
    agent_id: int
    client_id: int | None = None
    property_id: int | None = None
    channel: str
    direction: str
    subject: str | None = None
    body: str
    recipient: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    messages: list[MessageResponse] = Field(default_factory=list)
    total: int = 0
