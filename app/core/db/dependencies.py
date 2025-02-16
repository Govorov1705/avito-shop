from app.core.db.engine import async_session


async def get_session():
    async with async_session() as session:
        yield session
