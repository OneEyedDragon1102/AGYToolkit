from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status

from {{PACKAGE_NAME}}.schemas.item import ItemCreate, ItemResponse
from {{PACKAGE_NAME}}.services.item_service import item_service

router = APIRouter(prefix="/api/v1/items", tags=["items"])


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate) -> ItemResponse:
    return item_service.create(payload)


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: UUID) -> ItemResponse:
    item = item_service.get_by_id(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id '{item_id}' not found",
        )
    return item


@router.get("", response_model=List[ItemResponse])
def list_items() -> List[ItemResponse]:
    return item_service.list_all()
