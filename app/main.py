from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.db.populate import populate_db
from .api.v1.auth.routes import router as auth_router
from .api.v1.store.routes import router as store_router
from .core.db.engine import engine
from .core.db.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await populate_db()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router, prefix="/api")
app.include_router(store_router, prefix="/api")
