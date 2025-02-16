from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.store.models import Item


class ItemService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_item_by_type(self, type: str):
        result = await self.session.execute(select(Item).filter_by(type=type))
        return result.scalar()
