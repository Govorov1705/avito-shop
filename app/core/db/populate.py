from sqlalchemy import select
from .engine import async_session
from app.api.v1.store.schemas import Item as ItemSchema
from app.api.v1.store.models import Item


async def populate_db():
    items = [
        ItemSchema(type="t-shirt", cost=80),
        ItemSchema(type="cup", cost=20),
        ItemSchema(type="book", cost=50),
        ItemSchema(type="pen", cost=10),
        ItemSchema(type="powerbank", cost=200),
        ItemSchema(type="hoody", cost=300),
        ItemSchema(type="umbrella", cost=200),
        ItemSchema(type="socks", cost=10),
        ItemSchema(type="wallet", cost=50),
        ItemSchema(type="pink-hoody", cost=500),
    ]
    async with async_session() as session:
        for item in items:
            result = await session.execute(select(Item).filter_by(type=item.type))
            item_in_db = result.scalar()
            if not item_in_db:
                item_to_add = Item(type=item.type, cost=item.cost)
                session.add(item_to_add)
        await session.commit()
