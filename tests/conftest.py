import os

os.environ["APP_DATABASE_URL"] = "sqlite:///:memory:"
os.environ["APP_JWT_SECRET"] = "test-secret"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# 创建内存数据库 engine（StaticPool 保证所有连接共享同一个内存DB）
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=TEST_ENGINE
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# 覆盖依赖注入
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def _prepare_db():
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture(autouse=True)
def cleanup_tables():
    yield
    # 测试结束后清理所有表数据
    for table in reversed(Base.metadata.sorted_tables):
        with TEST_ENGINE.begin() as conn:
            conn.execute(table.delete())


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def token(client: TestClient) -> str:
    register_payload = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "Passw0rd!",
    }
    r = client.post("/auth/register", json=register_payload)
    assert r.status_code == 201

    login = client.post(
        "/auth/login",
        data={
            "username": register_payload["username"],
            "password": register_payload["password"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login.status_code == 200
    return login.json()["access_token"]
