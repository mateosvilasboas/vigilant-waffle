from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Desafio Técnico Luizalabs//Estante Virtual"
    VERSION: str = "0.1"
    DB_CONFIG: str = "sqlite+aiosqlite:///desafio.db"

settings = Settings()
