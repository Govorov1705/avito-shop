from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.api.v1.store.models import Inventory, InventoryItem, Item
from app.api.v1.store.schemas import Item as ItemSchema


class InventoryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_inventory_for_user(self, user_id: int) -> Inventory:
        result = await self.session.execute(
            insert(Inventory)
            .values(user_id=user_id)
            .on_conflict_do_nothing(index_elements=["user_id"])
            .returning(Inventory)
        )

        inventory = result.scalar()

        if not inventory:
            result = await self.session.execute(
                select(Inventory).filter_by(user_id=user_id)
            )
            inventory = result.scalar()

        await self.session.flush()

        return inventory

    async def get_inventory_items(self, inventory_id: int) -> list[InventoryItem]:
        result = await self.session.execute(
            select(InventoryItem, Item)
            .join(Item, InventoryItem.item_id == Item.id)
            .filter(InventoryItem.inventory_id == inventory_id)
        )

        items = []
        for item in result:
            for _ in range(item[0].quantity):
                items.append(ItemSchema(type=item[1].type, cost=item[1].cost))

        return items
