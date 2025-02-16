from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.api.v1.auth.models import User
from app.api.v1.store.models import Transaction, TransactionType
from app.api.v1.store.schemas import TransactionFromUser, TransactionToUser


class TransactionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_transaction(
        self,
        user_id: int,
        amount: int,
        type: TransactionType,
        recipient_id: int = None,
        item_id: int = None,
    ) -> Transaction | None:

        if not recipient_id and not item_id:
            return None

        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            type=type,
            timestamp=datetime.now(),
            recipient_id=recipient_id,
            item_id=item_id,
        )

        self.session.add(transaction)
        await self.session.flush()
        await self.session.refresh(transaction)

        return transaction

    async def get_sent_transactions(self, user_id: int) -> list[Transaction]:
        result = await self.session.execute(
            select(Transaction, User)
            .join(User, Transaction.recipient_id == User.id)
            .filter(
                Transaction.user_id == user_id, Transaction.type == TransactionType.GIFT
            )
        )

        return [
            TransactionToUser(
                toUser=transaction[1].username, amount=transaction[0].amount
            )
            for transaction in result
        ]

    async def get_received_transactions(self, user_id: int) -> list[Transaction]:
        result = await self.session.execute(
            select(Transaction, User)
            .join(User, Transaction.user_id == User.id)
            .filter(Transaction.recipient_id == user_id)
        )

        return [
            TransactionFromUser(
                fromUser=transaction[1].username, amount=transaction[0].amount
            )
            for transaction in result
        ]
