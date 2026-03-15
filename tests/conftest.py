import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["APP_DATABASE_URL"] = "sqlite:///./test_teketon_demo.db"
os.environ["APP_JWT_SECRET"] = "test-secret"

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _prepare_db_file():
    db_file = Path("test_teketon_demo.db")
    if db_file.exists():
        db_file.unlink()
    Base.metadata.create_all(bind=engine)
    yield
    if db_file.exists():
        db_file.unlink()


@pytest.fixture(autouse=True)
def cleanup_tables():
    for table in reversed(Base.metadata.sorted_tables):
        with engine.begin() as conn:
            conn.execute(table.delete())
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def token(client: TestClient) -> str:
    register_payload = {"username": "alice", "email": "alice@example.com", "password": "Passw0rd!"}
    r = client.post("/auth/register", json=register_payload)
    assert r.status_code == 201

    login = client.post(
        "/auth/login",
        data={"username": register_payload["username"], "password": register_payload["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login.status_code == 200
    return login.json()["access_token"]
