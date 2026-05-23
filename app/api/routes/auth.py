from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.config import get_settings
from app.core.logging import get_logger
from app.core.oauth_state import consume_state, generate_state
from app.core.rate_limit import limiter
from app.core.security import create_access_token, encrypt
from app.db.models import User
from app.schemas.auth import LoginInitResponse, LoginResponse
from app.services import oauth

logger = get_logger(__name__)
router = APIRouter()


@router.get("/google/login", response_model=LoginInitResponse)
@limiter.limit("10/minute")
async def google_login(request: Request) -> LoginInitResponse:
    state = await generate_state()
    return LoginInitResponse(authorize_url=oauth.build_authorize_url(state), state=state)


@router.get("/google/callback")
@limiter.limit("10/minute")
async def google_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    if not await consume_state(state):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid or expired state")

    tokens = await oauth.exchange_code(code)
    refresh_token = tokens.get("refresh_token")
    access_token = tokens.get("access_token")
    if not refresh_token or not access_token:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "google did not return a refresh_token; revoke prior app consent and retry",
        )

    info = await oauth.fetch_userinfo(access_token)
    email = info.get("email")
    if not email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "userinfo missing email")

    user = await db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            email=email,
            full_name=info.get("name"),
            google_refresh_token=encrypt(refresh_token),
        )
        db.add(user)
        logger.info("auth.user_created", email=email)
    else:
        user.google_refresh_token = encrypt(refresh_token)
        if info.get("name") and not user.full_name:
            user.full_name = info["name"]
        logger.info("auth.user_reauthorized", email=email)

    await db.commit()
    await db.refresh(user)

    jwt_token = create_access_token(subject=str(user.id), email=user.email)

    settings = get_settings()
    if settings.frontend_url:
        params = urlencode(
            {"token": jwt_token, "user_id": str(user.id), "email": user.email}
        )
        return RedirectResponse(
            url=f"{settings.frontend_url}/auth/callback?{params}",
            status_code=status.HTTP_302_FOUND,
        )

    return LoginResponse(
        access_token=jwt_token,
        token_type="bearer",
        user_id=str(user.id),
        email=user.email,
    )
