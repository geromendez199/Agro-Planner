import asyncio
import os
from datetime import date

import pytest
from fastapi.testclient import TestClient

# Configuración de entorno antes de importar la aplicación
os.environ.setdefault("CLIENT_ID", "test-client")
os.environ.setdefault("CLIENT_SECRET", "test-secret")
os.environ.setdefault("ORG_ID", "test-org")
os.environ.setdefault("JD_AUTH_URL", "https://example.com/auth")
os.environ.setdefault("JD_API_BASE", "https://example.com/api")
os.environ.setdefault("SECRET_KEY", "testing-secret")
os.environ.setdefault("DB_URL", "sqlite+aiosqlite:///./test_agroplanner.db")
os.environ.setdefault("SCHEDULER_INTERVAL_SECONDS", "0")
os.environ.setdefault("JD_FAKE_TOKEN", "fake-token")

from backend.app.main import app, get_client
from backend.app.database import get_engine, get_sessionmaker
from backend.app.models import Base, Field, Machine


class FakeJohnDeereClient:
    async def list_equipment(self, *args, **kwargs):
        return {"values": []}

    async def list_fields(self, *args, **kwargs):
        return {"values": []}

    async def list_field_operations(self, *args, **kwargs):
        return {"values": []}

    async def get_measurements(self, *args, **kwargs):
        return {"values": []}

    async def create_work_plan(self, *args, **kwargs):
        return {"id": "remote"}

    async def update_work_plan(self, *args, **kwargs):
        return {}

    async def delete_work_plan(self, *args, **kwargs):
        return {}


@pytest.fixture(autouse=True, scope="module")
def override_client():
    app.dependency_overrides[get_client] = lambda: FakeJohnDeereClient()
    yield
    app.dependency_overrides.pop(get_client, None)


@pytest.fixture(autouse=True)
def reset_db():
    async def _reset() -> None:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_reset())
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_register_login_and_work_plan_flow(client: TestClient):
    register_payload = {"username": "admin", "password": "secret", "role": "admin"}
    response = client.post("/auth/register", json=register_payload)
    assert response.status_code == 201

    login_response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "secret"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Crear campo y máquina para validar endpoints
    async def seed() -> None:
        session_factory = get_sessionmaker()
        async with session_factory() as session:
            session.add(Field(id="field-1", name="Campo 1"))
            session.add(Machine(id="machine-1", name="Cosechadora"))
            await session.commit()

    asyncio.run(seed())

    work_plan_payload = {
        "field_id": "field-1",
        "type": "SIEMBRA",
        "start_date": date(2024, 1, 1).isoformat(),
        "end_date": date(2024, 1, 2).isoformat(),
    }
    create_plan = client.post("/work-plans", json=work_plan_payload, headers=headers)
    assert create_plan.status_code == 201
    plan_id = create_plan.json()["id"]

    plans_list = client.get("/work-plans", headers=headers)
    assert plans_list.status_code == 200
    assert len(plans_list.json()) == 1

    machines_response = client.get("/machines", headers=headers)
    assert machines_response.status_code == 200
    assert machines_response.json()[0]["id"] == "machine-1"

    scheduler_status = client.get("/scheduler/status", headers=headers)
    assert scheduler_status.status_code == 200
    assert scheduler_status.json()["running"] is False

    update_response = client.put(
        f"/work-plans/{plan_id}", json={"status": "completed"}, headers=headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "completed"

    delete_response = client.delete(f"/work-plans/{plan_id}", headers=headers)
    assert delete_response.status_code == 204


def test_register_requires_admin_when_users_exist(client: TestClient):
    client.post("/auth/register", json={"username": "admin", "password": "secret", "role": "admin"})
    login = client.post(
        "/auth/login",
        data={"username": "admin", "password": "secret"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/auth/register",
        json={"username": "operator", "password": "secret", "role": "operator"},
        headers=headers,
    )
    assert response.status_code == 201

    forbidden = client.post(
        "/auth/register",
        json={"username": "outsider", "password": "secret", "role": "operator"},
    )
    assert forbidden.status_code == 403
