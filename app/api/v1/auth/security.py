from passlib.context import CryptContext
from jwt import InvalidTokenError, decode, encode
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.api.v1.auth.models import User
from .schemas import AuthRequest


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_jwt(data: dict):
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    to_encode.update(
        iat=now,
        exp=now + settings.JWT_LIFESPAN,
    )
    return encode(
        payload=to_encode,
        key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_jwt(token: str):
    return decode(
        token,
        settings.SECRET_KEY,
        [settings.ALGORITHM],
    )


def get_sub_from_token(token: str):
    token_payload = decode_jwt(token)

    token_sub = token_payload.get("sub")
    if not token_sub:
        raise InvalidTokenError("Token does not contain 'sub' field")

    return token_sub
