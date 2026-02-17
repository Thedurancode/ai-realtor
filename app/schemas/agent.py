from pydantic import BaseModel, EmailStr
from datetime import datetime


class AgentBase(BaseModel):
    email: EmailStr
    name: str
    phone: str | None = None
    license_number: str | None = None


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    email: EmailStr | None = None
    name: str | None = None
    phone: str | None = None
    license_number: str | None = None


class AgentRegister(BaseModel):
    email: EmailStr
    name: str
    phone: str | None = None
    license_number: str | None = None


class AgentRegisterResponse(BaseModel):
    id: int
    name: str
    email: str
    api_key: str
    created_at: datetime

    class Config:
        from_attributes = True


class AgentResponse(AgentBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
