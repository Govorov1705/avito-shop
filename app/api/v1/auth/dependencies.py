from fastapi import Depends
from typing import Annotated
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.api.v1.auth.services.user_service import UserService
from app.core.db.dependencies import get_session
from .models import User
from .security import get_sub_from_token


auth_scheme = HTTPBearer(auto_error=False)


def get_user_from_jwt_factory(for_update: bool = False):
    async def get_user_from_jwt(
        session: Annotated[AsyncSession, Depends(get_session)],
        credentials: Annotated[HTTPAuthorizationCredentials, Depends(auth_scheme)],
    ) -> User:
        user_service = UserService(session)
        try:
            if not credentials:
                return None

            token = credentials.credentials
            user_id = get_sub_from_token(token)
            user = await user_service.get_user_by_id(int(user_id), for_update)

            if not user:
                raise InvalidTokenError("Invalid token sub")

            return user

        except InvalidTokenError as e:
            return None

    return get_user_from_jwt
