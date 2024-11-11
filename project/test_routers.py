import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from models import table_registry
from database import get_db

SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///test.db"

engine = create_async_engine(SQLALCHEMY_TEST_DATABASE_URL)
TestSessionManager = async_sessionmaker(engine, expire_on_commit=False)

@pytest_asyncio.fixture(autouse=True, scope="module")
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.drop_all)


@pytest_asyncio.fixture
async def async_session():
    async with TestSessionManager() as session:
        yield session

@pytest_asyncio.fixture
async def client(async_session):
    def override_get_db():
        yield async_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as client:
        yield client
    app.dependency_overrides = {}

# --- tests functions ---

@pytest.mark.asyncio
async def test_get_competitions_empty(client: AsyncClient):  
    response = await client.get("/api/get-competitions")
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_ranking_empty(client: AsyncClient):
    response = await client.get("/api/get-ranking")
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_create_competition_success(client: AsyncClient):
    json = {"name": "corrida 100m",
            "unit": "seconds",
            "number_of_attempts": 1}
    response = await client.post("/api/create-competition", json=json)
    assert response.status_code == status.HTTP_201_CREATED

    assert response.json()["competition"]["name"] == "corrida 100m"

    json = {"name": "dardos ",
            "unit": "seconds",
            "number_of_attempts": 1}
    response = await client.post("/api/create-competition", json=json)
    assert response.status_code == status.HTTP_201_CREATED

    assert response.json()["competition"]["name"] == "dardos"

    json = {"name": " levantamento",
            "unit": "seconds",
            "number_of_attempts": 1}
    response = await client.post("/api/create-competition", json=json)
    assert response.status_code == status.HTTP_201_CREATED

    assert response.json()["competition"]["name"] == "levantamento"

@pytest.mark.asyncio
async def test_create_competition_without_name(client: AsyncClient):
    json = {"name": "",
            "unit": "seconds",
            "number_of_attempts": 1}
    response = await client.post("/api/create-competition", json=json)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_get_competitions_success(client: AsyncClient):
    response = await client.get("/api/get-competitions")
    assert response.status_code == status.HTTP_200_OK

    assert len(response.json()) == 1

    assert response.json()["competitions"][0]["name"] == "corrida 100m"
    assert response.json()["competitions"][0]["unit"] == "seconds"
    assert response.json()["competitions"][0]["number_of_attempts"] == 1

@pytest.mark.asyncio
async def test_create_competition_unique_name_failed(client: AsyncClient):
    json = {"name": "corrida 100m",
            "unit": "seconds",
            "number_of_attempts": 1}
    response = await client.post("/api/create-competition", json=json)
    assert response.status_code == status.HTTP_409_CONFLICT
    
@pytest.mark.asyncio
async def test_create_competition_unit_failed(client: AsyncClient):
    json = {"name": "salto",
            "unit": "meeters",
            "number_of_attempts": 3}
    response = await client.post("/api/create-competition", json=json)
    assert response.status_code == status.HTTP_409_CONFLICT

@pytest.mark.asyncio
async def test_create_result_success(client: AsyncClient):
    json = {"competition": "corrida 100m",
            "athlete": "mateus",
            "scores": [2.2]}
    response = await client.post("/api/create-result", json=json)
    assert response.status_code == status.HTTP_201_CREATED

    assert response.json()["new_result"]["competition_id"] == 1
    assert response.json()["new_result"]["name"] == "mateus"
    assert response.json()["new_result"]["scores"][0]["value"] == 2.2

    json = {"competition": "corrida 100m",
            "athlete": "joao ",
            "scores": [1.0]}

    response = await client.post("/api/create-result", json=json)
    assert response.status_code == status.HTTP_201_CREATED

    assert response.json()["new_result"]["name"] == "joao"

    json = {"competition": "corrida 100m",
           "athlete": " lucas",
           "scores": [4.0]}
    
    response = await client.post("/api/create-result", json=json)
    assert response.status_code == status.HTTP_201_CREATED

    assert response.json()["new_result"]["name"] == "lucas"

@pytest.mark.asyncio
async def test_create_result_without_athlete(client: AsyncClient):
    json = {"competition": "corrida 100m",
            "athlete": "",
            "scores": [2.2]}
    response = await client.post("/api/create-result", json=json)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_create_result_competition_not_found(client: AsyncClient):
    json = {"competition": "boxe",
            "athlete": "mateus",
            "scores": [2.2]}
    response = await client.post("/api/create-result", json=json)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_create_result_different_number_of_attempts(client: AsyncClient):
    json = {"competition": "corrida 100m",
            "athlete": "mateus",
            "scores": [2.2, 1.1]}
    response = await client.post("/api/create-result", json=json)
    assert response.status_code == status.HTTP_409_CONFLICT

@pytest.mark.asyncio
async def test_change_competition_status_success(client: AsyncClient):
    json = {"id": 1}
    response = await client.put("/api/change-competition-status", json=json)

    assert response.status_code == status.HTTP_200_OK
    
    assert response.json()["competition"]["id"] == 1
    assert response.json()["competition"]["is_finished"] == True

@pytest.mark.asyncio
async def test_change_competition_status_not_found(client: AsyncClient):
    json = {"id": 4}
    response = await client.put("/api/change-competition-status", json=json)

    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_create_result_competition_is_finished(client: AsyncClient):
    json = {"competition": "corrida 100m",
            "athlete": "mateus",
            "scores": [2.2]}
    response = await client.post("/api/create-result", json=json)
    assert response.status_code == status.HTTP_409_CONFLICT

@pytest.mark.asyncio
async def test_get_ranking_success(client: AsyncClient):
    response = await client.get("/api/get-ranking/corrida 100m")    
    assert response.status_code == status.HTTP_200_OK

    assert response.json()["ranking"][0]["athlete"] == "joao"
    assert response.json()["ranking"][0]["best_score"] == 1.0
