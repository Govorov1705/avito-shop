from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime


from app.api.v1.auth.models import User
from app.api.v1.auth.security import get_password_hash, verify_password


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_id(self, id: int, for_update: bool = False) -> User | None:
        query = select(User).filter_by(id=id)

        if for_update:
            query = query.with_for_update()

        result = await self.session.execute(query)
        user = result.scalar()

        if not user:
            return None

        return user

    async def get_user_by_username(
        self, username: str, for_update: bool = None
    ) -> User | None:
        query = select(User).filter_by(username=username)

        if for_update:
            query = query.with_for_update()

        result = await self.session.execute(query)
        user = result.scalar()

        if not user:
            return None

        return user

    async def get_or_create_user(self, username: str, password: str) -> User:
        hashed_password = get_password_hash(password)

        result = await self.session.execute(
            insert(User)
            .values(
                username=username,
                password=hashed_password,
                created_at=datetime.now(),
                coins=1000,
            )
            .on_conflict_do_nothing(index_elements=["username"])
            .returning(User)
        )

        user = result.scalar()

        if not user:
            result = await self.session.execute(
                select(User).filter_by(username=username)
            )
            user = result.scalar()

        return user

    async def authenticate_user(self, username: str, password: str) -> bool:
        result = await self.session.execute(select(User).filter_by(username=username))
        user = result.scalar()

        if not user:
            return False

        if not verify_password(password, user.password):
            return False

        return True
