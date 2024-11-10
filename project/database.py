from sqlalchemy.ext.asyncio import (async_sessionmaker, create_async_engine)

from models import table_registry
from config import settings

engine = create_async_engine(settings.DB_CONFIG, connect_args={"check_same_thread": False})
SessionManager = async_sessionmaker(engine)

async def get_db():
    async with SessionManager() as db: 
        yield db