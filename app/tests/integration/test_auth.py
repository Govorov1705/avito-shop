import pytest
import uuid

from app.api.v1.auth.schemas import AuthRequest
from app.api.v1.auth.services.user_service import UserService


pytestmark = pytest.mark.anyio


async def test_auth_new_user(client):
    response = await client.post(
        "/auth",
        json={
            "username": f"user_{uuid.uuid4()}",
            "password": "Secretpassword",
        },
    )
    assert response.status_code == 200
    assert "token" in response.json()


async def test_auth_existing_user(client, session):
    auth_request = AuthRequest(
        username=f"user_{uuid.uuid4()}",
        password="Secretpassword",
    )

    user_service = UserService(session)
    user = await user_service.get_or_create_user(
        username=auth_request.username, password=auth_request.password
    )
    await session.commit()

    response = await client.post(
        "/auth",
        json={
            "username": user.username,
            "password": "Secretpassword",
        },
    )
    assert response.status_code == 200
    assert "token" in response.json()


async def test_auth_wrong_password(client, session):
    auth_request = AuthRequest(
        username=f"user_{uuid.uuid4()}",
        password="Secretpassword",
    )

    user_service = UserService(session)
    user = await user_service.get_or_create_user(
        username=auth_request.username, password=auth_request.password
    )
    await session.commit()

    response = await client.post(
        "/auth",
        json={
            "username": user.username,
            "password": "Wrongpassword",
        },
    )

    assert response.status_code == 401
    assert "token" not in response.json()


async def test_auth_missing_field(client):
    response = await client.post(
        "/auth",
        json={"password": "Wrongpassword"},
    )

    assert response.status_code == 422
    assert "token" not in response.json()
