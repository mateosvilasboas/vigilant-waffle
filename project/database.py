from sqlalchemy.ext.asyncio import (AsyncConnection, AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)

from models import table_registry
from config import settings

engine = create_async_engine(settings.DB_CONFIG, connect_args={"check_same_thread": False})
SessionManager = async_sessionmaker(engine)

async def get_db():

    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.create_all)

    db = SessionManager()
    try: 
        yield db
    finally:
        await db.close()