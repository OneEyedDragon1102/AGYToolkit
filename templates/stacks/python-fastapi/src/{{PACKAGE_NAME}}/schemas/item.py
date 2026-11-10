from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Item name must not be empty")
    price: float = Field(..., ge=0.0, description="Item price must be non-negative")


class ItemResponse(BaseModel):
    id: UUID
    name: str
    price: float
    created_at: datetime
