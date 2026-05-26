from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from pydantic import BaseModel

router = APIRouter()


class LoginRequest(BaseModel):

    username: str

    password: str


class TokenResponse(BaseModel):

    access_token: str

    refresh_token: str

    token_type: str = "bearer"


@router.post(
    "/login",
    response_model=TokenResponse
)
async def login(
    payload: LoginRequest
):

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Auth not yet implemented"
    )


@router.post(
    "/refresh",
    response_model=TokenResponse
)
async def refresh_token(
    refresh_token: str
):

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh not yet implemented"
    )
