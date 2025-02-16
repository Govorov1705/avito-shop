import pytest
import asyncpg
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import settings
from app.core.db.base import Base
from app.core.db.dependencies import get_session
from app.api.v1.store.schemas import Item as ItemSchema
from ..main import app

from app.api.v1.auth.models import *
from app.api.v1.store.models import *


# Sets the anyio scope to "session" to avoid conflicts
# with custom fixtures' scopes.
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


# Create test db if non existant.
@pytest.fixture(scope="session", autouse=True)
async def create_test_db():
    conn = await asyncpg.connect(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        database="postgres",
    )
    exists = await conn.fetchval(
        "SELECT 1 FROM pg_database WHERE datname = $1", settings.TESTING_DB_NAME
    )
    if not exists:
        await conn.execute(f'CREATE DATABASE "{settings.TESTING_DB_NAME}"')
    await conn.close()


@pytest.fixture(autouse=True)
async def db_tables_lifecycle():
    engine = create_async_engine(url=settings.TESTING_DB_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

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

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(name="session")
async def session_fixture():
    engine = create_async_engine(url=settings.TESTING_DB_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture(name="client")
async def client_fixture(session: AsyncSession):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost/api"
    ) as client:
        yield client
    app.dependency_overrides.clear()
