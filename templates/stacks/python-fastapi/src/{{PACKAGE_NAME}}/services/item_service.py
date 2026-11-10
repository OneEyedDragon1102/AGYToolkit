from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from {{PACKAGE_NAME}}.schemas.item import ItemCreate, ItemResponse


class ItemService:
    def __init__(self) -> None:
        self._items: Dict[UUID, ItemResponse] = {}

    def create(self, data: ItemCreate) -> ItemResponse:
        item = ItemResponse(
            id=uuid4(),
            name=data.name.strip(),
            price=data.price,
            created_at=datetime.now(timezone.utc),
        )
        self._items[item.id] = item
        return item

    def get_by_id(self, item_id: UUID) -> Optional[ItemResponse]:
        return self._items.get(item_id)

    def list_all(self) -> List[ItemResponse]:
        return list(self._items.values())

    def clear(self) -> None:
        self._items.clear()


item_service = ItemService()
