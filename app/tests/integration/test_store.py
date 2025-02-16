import pytest
import uuid
from sqlalchemy import select

from app.api.v1.auth.models import User
from app.api.v1.auth.services.user_service import UserService
from app.api.v1.store.models import (
    Inventory,
    InventoryItem,
    Transaction,
    Item,
    TransactionType,
)


pytestmark = pytest.mark.anyio


async def test_buy_item(client, session):
    username = f"user_{uuid.uuid4()}"

    response = await client.post(
        "/auth",
        json={
            "username": username,
            "password": "Secretpassword",
        },
    )
    token = response.json()["token"]

    response = await client.get(
        "/buy/pink-hoody", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    result = await session.execute(select(User).filter_by(username=username))
    user = result.scalar()
    assert user
    assert user.coins == 500

    result = await session.execute(select(Inventory).filter_by(user_id=user.id))
    inventory = result.scalar()
    assert inventory

    result = await session.execute(
        select(InventoryItem).filter_by(inventory_id=inventory.id)
    )
    inventory_item = result.scalar()
    assert inventory_item

    result = await session.execute(select(Item).filter_by(id=inventory_item.item_id))
    item = result.scalar()
    assert item
    assert item.type == "pink-hoody"

    result = await session.execute(select(Transaction).filter_by(user_id=user.id))
    transaction = result.scalar()
    assert transaction
    assert transaction.amount == 500
    assert transaction.item_id == item.id


async def test_buy_item_not_authenticated(client, session):
    username = f"user_{uuid.uuid4()}"

    response = await client.post(
        "/auth",
        json={
            "username": username,
            "password": "Secretpassword",
        },
    )

    response = await client.get("/buy/pink-hoody")
    assert response.status_code == 401

    result = await session.execute(select(User).filter_by(username=username))
    user = result.scalar()
    assert user
    assert user.coins == 1000

    result = await session.execute(select(Inventory).filter_by(user_id=user.id))
    inventory = result.scalar()
    assert not inventory

    result = await session.execute(select(Transaction).filter_by(user_id=user.id))
    transaction = result.scalar()
    assert not transaction


async def test_buy_same_item(client, session):
    username = f"user_{uuid.uuid4()}"

    response = await client.post(
        "/auth",
        json={
            "username": username,
            "password": "Secretpassword",
        },
    )
    token = response.json()["token"]

    response = await client.get(
        "/buy/pink-hoody", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    result = await session.execute(select(User).filter_by(username=username))
    user = result.scalar()
    assert user
    assert user.coins == 500

    result = await session.execute(select(Inventory).filter_by(user_id=user.id))
    inventory = result.scalar()
    assert inventory

    result = await session.execute(
        select(InventoryItem).filter_by(inventory_id=inventory.id)
    )
    inventory_item = result.scalar()
    assert inventory_item

    result = await session.execute(select(Item).filter_by(id=inventory_item.item_id))
    item = result.scalar()
    assert item
    assert item.type == "pink-hoody"

    result = await session.execute(select(Transaction).filter_by(user_id=user.id))
    first_transaction = result.scalar()
    assert first_transaction
    assert first_transaction.amount == 500
    assert first_transaction.item_id == item.id

    # Buy the same item
    response = await client.get(
        "/buy/pink-hoody", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    await session.refresh(user)
    await session.refresh(inventory_item)

    assert user.coins == 0
    assert inventory_item.quantity == 2

    result = await session.execute(
        select(Transaction)
        .filter_by(user_id=user.id)
        .filter(Transaction.id != first_transaction.id)
    )
    second_transaction = result.scalar()
    assert second_transaction
    assert second_transaction.amount == 500
    assert second_transaction.item_id == item.id


async def test_buy_item_insufficient_balance(client, session):
    username = f"user_{uuid.uuid4()}"

    response = await client.post(
        "/auth",
        json={
            "username": username,
            "password": "Secretpassword",
        },
    )
    token = response.json()["token"]

    result = await session.execute(select(User).filter_by(username=username))
    user = result.scalar()
    assert user
    user.coins = 0
    await session.flush()

    response = await client.get(
        "/buy/pink-hoody", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert response.json()["errors"] == "You don't have enough coins"

    assert user.coins == 0

    result = await session.execute(select(Inventory).filter_by(user_id=user.id))
    inventory = result.scalar()
    assert not inventory

    result = await session.execute(select(Transaction).filter_by(user_id=user.id))
    transaction = result.scalar()
    assert not transaction


async def test_send_coin_not_authenticated(client, session):
    username = f"user_{uuid.uuid4()}"

    response = await client.post(
        "/auth",
        json={
            "username": username,
            "password": "Secretpassword",
        },
    )

    result = await session.execute(select(User).filter_by(username=username))
    user = result.scalar()
    assert user
    assert user.coins == 1000

    user_service = UserService(session)
    recipient = await user_service.get_or_create_user(
        username="recipient_user", password="Secretpassword"
    )
    await session.commit()
    assert recipient
    assert recipient.coins == 1000

    response = await client.post(
        "/sendCoin",
        json={"amount": 350, "toUser": recipient.username},
    )
    assert response.status_code == 401
    assert user.coins == 1000
    assert recipient.coins == 1000

    result = await session.execute(
        select(Transaction).filter_by(user_id=user.id, recipient_id=recipient.id)
    )
    transaction = result.scalar()

    assert not transaction


async def test_send_coin(client, session):
    username = f"user_{uuid.uuid4()}"

    response = await client.post(
        "/auth",
        json={
            "username": username,
            "password": "Secretpassword",
        },
    )
    token = response.json()["token"]

    result = await session.execute(select(User).filter_by(username=username))
    user = result.scalar()
    assert user
    assert user.coins == 1000

    user_service = UserService(session)
    recipient = await user_service.get_or_create_user(
        username="recipient_user", password="Secretpassword"
    )
    await session.commit()
    assert recipient
    assert recipient.coins == 1000

    response = await client.post(
        "/sendCoin",
        json={"amount": 350, "toUser": recipient.username},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert user.coins == 650
    assert recipient.coins == 1350

    result = await session.execute(
        select(Transaction).filter_by(user_id=user.id, recipient_id=recipient.id)
    )
    transaction = result.scalar()

    assert transaction
    assert transaction.type == TransactionType.GIFT
    assert transaction.amount == 350


async def test_send_coin_insufficient_balance(client, session):
    username = f"user_{uuid.uuid4()}"

    response = await client.post(
        "/auth",
        json={
            "username": username,
            "password": "Secretpassword",
        },
    )
    token = response.json()["token"]

    result = await session.execute(select(User).filter_by(username=username))
    user = result.scalar()
    assert user
    user.coins = 0
    await session.flush()

    user_service = UserService(session)
    recipient = await user_service.get_or_create_user(
        username="recipient_user", password="Secretpassword"
    )
    await session.commit()
    assert recipient
    assert recipient.coins == 1000

    response = await client.post(
        "/sendCoin",
        json={"amount": 350, "toUser": recipient.username},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert user.coins == 0
    assert recipient.coins == 1000

    result = await session.execute(
        select(Transaction).filter_by(user_id=user.id, recipient_id=recipient.id)
    )
    transaction = result.scalar()

    assert not transaction


async def test_send_coin_invalid_recipient(client, session):
    username = f"user_{uuid.uuid4()}"

    response = await client.post(
        "/auth",
        json={
            "username": username,
            "password": "Secretpassword",
        },
    )
    token = response.json()["token"]

    result = await session.execute(select(User).filter_by(username=username))
    user = result.scalar()
    assert user
    assert user.coins == 1000

    response = await client.post(
        "/sendCoin",
        json={"amount": 350, "toUser": "non-existant-recipient"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert user.coins == 1000

    result = await session.execute(
        select(Transaction).filter_by(user_id=user.id, type=TransactionType.GIFT)
    )
    transaction = result.scalar()

    assert not transaction
