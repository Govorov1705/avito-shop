from fastapi import APIRouter, Depends, status, Response
from typing import Annotated
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.services.user_service import UserService
from app.api.v1.schemas import ErrorResponse
from app.api.v1.store.services.inventory_item_service import InventoryItemService
from app.api.v1.store.services.inventory_service import InventoryService
from app.api.v1.store.services.item_service import ItemService
from app.api.v1.store.services.transaction_service import TransactionService
from .models import TransactionType
from app.api.v1.auth.models import User
from app.api.v1.auth.dependencies import get_user_from_jwt_factory
from app.core.db.dependencies import get_session
from .schemas import (
    InfoResponse,
    CoinHistory,
    SendCoinRequest,
)


router = APIRouter()


@router.get(
    "/buy/{item}",
    response_class=Response,
    responses={
        401: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
        500: {},
    },
)
async def buy_item(
    item: str,
    user: Annotated[User, Depends(get_user_from_jwt_factory(for_update=True))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    if not user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(errors="Invalid token").model_dump(),
        )

    item_service = ItemService(session)
    inventory_service = InventoryService(session)
    inventory_item_service = InventoryItemService(session)
    transcaction_service = TransactionService(session)

    item_obj = await item_service.get_item_by_type(item)
    if not item_obj:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(errors="Item does not exist").model_dump(),
        )

    # Check if user has enough coins
    if user.coins < item_obj.cost:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(errors="You don't have enough coins").model_dump(),
        )

    inventory = await inventory_service.get_or_create_inventory_for_user(user.id)

    _ = await inventory_item_service.add_item_to_inventory(item_obj.id, inventory.id)

    # Subtract the cost from user's coins
    user.coins -= item_obj.cost

    _ = await transcaction_service.create_transaction(
        user_id=user.id,
        amount=item_obj.cost,
        type=TransactionType.PURCHASE,
        recipient_id=None,
        item_id=item_obj.id,
    )

    await session.commit()

    return Response(status_code=status.HTTP_200_OK)


@router.post(
    "/sendCoin",
    response_class=Response,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        500: {},
    },
)
async def send_coin(
    user: Annotated[User, Depends(get_user_from_jwt_factory(for_update=True))],
    session: Annotated[AsyncSession, Depends(get_session)],
    send_coin_request: SendCoinRequest,
):
    if not user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(errors="Invalid token").model_dump(),
        )

    # TODO: service
    if user.coins < send_coin_request.amount:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(errors="You don't have enough coins").model_dump(),
        )

    user_service = UserService(session)
    transaction_service = TransactionService(session)

    recipient = await user_service.get_user_by_username(
        send_coin_request.toUser, for_update=True
    )
    if not recipient:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(errors="recipient not found").model_dump(),
        )

    user.coins -= send_coin_request.amount
    recipient.coins += send_coin_request.amount

    _ = await transaction_service.create_transaction(
        user_id=user.id,
        amount=send_coin_request.amount,
        type=TransactionType.GIFT,
        recipient_id=recipient.id,
        item_id=None,
    )

    await session.commit()

    return Response(status_code=status.HTTP_200_OK)


@router.get(
    "/info",
    responses={
        401: {"model": ErrorResponse},
        500: {},
    },
)
async def info(
    user: Annotated[User, Depends(get_user_from_jwt_factory())],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> InfoResponse:
    if not user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(errors="Invalid token").model_dump(),
        )

    inventory_service = InventoryService(session)
    transactions_service = TransactionService(session)

    inventory = await inventory_service.get_or_create_inventory_for_user(user.id)

    items = await inventory_service.get_inventory_items(inventory.id)

    sent_transactions = await transactions_service.get_sent_transactions(user.id)

    received_transactions = await transactions_service.get_received_transactions(
        user.id
    )

    coin_history = CoinHistory(received=received_transactions, sent=sent_transactions)

    return InfoResponse(coins=user.coins, inventory=items, coinHistory=coin_history)
