from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings


engine = create_async_engine(url=settings.DB_URL, echo=settings.DB_ECHO)
async_session = async_sessionmaker(engine, expire_on_commit=False)
