from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.api.v1.store.models import InventoryItem


class InventoryItemService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_item_to_inventory(
        self, item_id: int, inventory_id: int
    ) -> InventoryItem:

        result = await self.session.execute(
            insert(InventoryItem)
            .values(inventory_id=inventory_id, item_id=item_id, quantity=1)
            .on_conflict_do_update(
                constraint="uq_inventory_item",
                set_=dict(quantity=InventoryItem.quantity + 1),
            )
            .returning(InventoryItem)
        )

        await self.session.flush()

        return result.scalar()
