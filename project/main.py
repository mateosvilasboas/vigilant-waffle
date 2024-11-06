# from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Desafio Técnico Luizalabs//Estante Virtual")

from routers import router as competition_router

app.include_router(competition_router, prefix="/api", tags=["competition"])

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8000)