from datetime import datetime

from pydantic import BaseModel, Field


class MediaCreate(BaseModel):
    property_id: int
    media_type: str = "photo"
    url: str
    filename: str | None = None
    caption: str | None = None
    sort_order: int = 0
    is_primary: int = 0


class MediaUpdate(BaseModel):
    caption: str | None = None
    sort_order: int | None = None
    is_primary: int | None = None


class MediaReorderItem(BaseModel):
    media_id: int
    sort_order: int


class MediaReorderRequest(BaseModel):
    items: list[MediaReorderItem]


class MediaResponse(BaseModel):
    id: int
    property_id: int
    media_type: str
    url: str
    filename: str | None = None
    caption: str | None = None
    sort_order: int
    is_primary: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class MediaListResponse(BaseModel):
    property_id: int
    media: list[MediaResponse] = Field(default_factory=list)
    total: int = 0
