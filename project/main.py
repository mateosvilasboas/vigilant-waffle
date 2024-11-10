from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from config import settings
from database import engine
from models import table_registry
from routers import router as competition_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.create_all)
        yield
    await engine.dispose()

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.include_router(competition_router, prefix="/api", tags=["competition"])

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8000)