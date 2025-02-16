import pytest
from sqlalchemy import func, select

from app.api.v1.auth.models import User
from app.api.v1.auth.security import get_password_hash
from app.api.v1.auth.services.user_service import UserService


pytestmark = pytest.mark.anyio


async def test_get_user_by_id(session):
    user_service = UserService(session)

    hashed_password = get_password_hash("Secretpassword")
    user = User(username="test_user", password=hashed_password)
    session.add(user)
    await session.flush()
    await session.refresh(user)

    user_from_query = await user_service.get_user_by_id(user.id)
    assert user.id == user_from_query.id


async def test_get_user_by_id_non_existant(session):
    user_service = UserService(session)
    user_id = 1

    user = await user_service.get_user_by_id(user_id)
    assert not user


async def test_get_user_by_username(session):
    user_service = UserService(session)

    hashed_password = get_password_hash("Secretpassword")
    user = User(username="test_user", password=hashed_password)
    session.add(user)
    await session.flush()
    await session.refresh(user)

    user_from_query = await user_service.get_user_by_username(user.username)
    assert user.username == user_from_query.username


async def test_get_user_by_username_non_existant(session):
    user_service = UserService(session)
    username = "test_user"

    user = await user_service.get_user_by_username(username)
    assert not user


async def test_get_or_create_user_new_user(session):
    user_service = UserService(session)
    username = "test_user"
    password = "Secretpassword"

    user = await user_service.get_or_create_user(username=username, password=password)
    assert user
    assert user.username == username

    # Check that we store hashed password
    assert user.password != password


async def test_get_or_create_user_existing_user(session):
    user_service = UserService(session)
    username = "test_user"
    password = "Secretpassword"
    hashed_password = get_password_hash(password)

    user = User(username=username, password=hashed_password)
    session.add(user)
    await session.flush()
    await session.refresh(user)

    user_from_query = await user_service.get_or_create_user(
        username=username, password=password
    )
    assert user_from_query
    assert user_from_query.id == user.id

    # Check that we store hashed password
    assert user_from_query.password != password

    # Check for no duplicates
    result = await session.execute(
        select(func.count()).select_from(User).filter_by(username=username)
    )
    count = result.scalar()
    assert count == 1


async def test_authenticate_user(session):
    user_service = UserService(session)

    hashed_password = get_password_hash("Secretpassword")
    user = User(username="test_user", password=hashed_password)
    session.add(user)
    await session.flush()
    await session.refresh(user)

    is_authenticated = await user_service.authenticate_user(
        "test_user", "Secretpassword"
    )
    assert is_authenticated


async def test_authenticate_user_wrong_password(session):
    user_service = UserService(session)

    hashed_password = get_password_hash("Secretpassword")
    user = User(username="test_user", password=hashed_password)
    session.add(user)
    await session.flush()
    await session.refresh(user)

    is_authenticated = await user_service.authenticate_user(
        "test_user", "Wrongpassword"
    )
    assert not is_authenticated
