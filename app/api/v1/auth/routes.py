from typing import Annotated
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.security import create_jwt
from app.api.v1.auth.services.user_service import UserService
from app.core.db.dependencies import get_session
from .schemas import AuthRequest, AuthResponse
from app.api.v1.schemas import ErrorResponse


router = APIRouter()


@router.post(
    "/auth",
    responses={
        401: {"model": ErrorResponse},
        500: {},
    },
)
async def auth(
    auth_request: AuthRequest,
    session: Annotated[
        AsyncSession,
        Depends(get_session),
    ],
) -> AuthResponse:
    user_service = UserService(session)
    user = await user_service.get_or_create_user(
        username=auth_request.username, password=auth_request.password
    )
    await session.commit()

    if not await user_service.authenticate_user(
        username=auth_request.username, password=auth_request.password
    ):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(errors="Invalid username or password").model_dump(),
        )

    token = create_jwt({"sub": str(user.id)})

    return AuthResponse(token=token)
