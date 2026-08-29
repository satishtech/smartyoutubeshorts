"""Auth routes: register/login/refresh/logout, Google OAuth, and profile."""
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth.google import build_authorization_url, exchange_code_for_tokens, fetch_google_userinfo, generate_state
from app.auth.jwt import create_access_token, create_refresh_token, hash_password, hash_token, verify_password
from app.auth.rate_limit import limiter
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import BadRequestError, ConflictError, UnauthorizedError
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, RegisterRequest, Token
from app.schemas.user import UserResponse, UserUpdateRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

STATE_COOKIE_NAME = "oauth_state"


def _issue_tokens(db: Session, user: User) -> Token:
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token, expires_at = create_refresh_token({"sub": str(user.id)})
    db.add(RefreshToken(user_id=user.id, token_hash=hash_token(refresh_token), expires_at=expires_at))
    db.commit()
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit("10/minute")
async def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    """Register a new user with email + password."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise ConflictError("An account with this email already exists")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    """Authenticate with email + password and receive access/refresh tokens."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise UnauthorizedError("Invalid email or password")
    if not user.is_active:
        raise UnauthorizedError("Account is inactive")
    return _issue_tokens(db, user)


@router.post("/refresh", response_model=Token)
@limiter.limit("30/minute")
async def refresh(request: Request, payload: RefreshRequest, db: Session = Depends(get_db)) -> Token:
    """Exchange a valid, unexpired, unrevoked refresh token for a new token pair (rotation)."""
    from app.auth.jwt import decode_token

    token_payload = decode_token(payload.refresh_token)
    if not token_payload or token_payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid refresh token")

    token_hash = hash_token(payload.refresh_token)
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if not stored or stored.revoked:
        raise UnauthorizedError("Refresh token has been revoked or is unknown")
    if stored.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        raise UnauthorizedError("Refresh token has expired")

    user = db.query(User).filter(User.id == stored.user_id).first()
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")

    # Rotate: revoke the old refresh token, issue a new pair.
    stored.revoked = True
    db.add(stored)
    db.commit()

    return _issue_tokens(db, user)


@router.post("/logout", status_code=204)
async def logout(payload: LogoutRequest, db: Session = Depends(get_db)) -> None:
    """Revoke a refresh token (idempotent — always succeeds)."""
    token_hash = hash_token(payload.refresh_token)
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if stored:
        stored.revoked = True
        db.add(stored)
        db.commit()


@router.get("/google")
async def google_login() -> RedirectResponse:
    """Redirect the browser to Google's OAuth consent screen, setting a CSRF state cookie."""
    if not settings.GOOGLE_CLIENT_ID:
        raise BadRequestError("Google OAuth is not configured")
    state = generate_state()
    response = RedirectResponse(url=build_authorization_url(state))
    response.set_cookie(
        STATE_COOKIE_NAME,
        state,
        max_age=600,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
    )
    return response


@router.get("/google/callback")
async def google_callback(request: Request, code: str, state: str, db: Session = Depends(get_db)) -> RedirectResponse:
    """Handle Google's redirect: verify CSRF state, exchange code, upsert user, issue tokens."""
    cookie_state = request.cookies.get(STATE_COOKIE_NAME)
    if not cookie_state or cookie_state != state:
        raise UnauthorizedError("Invalid OAuth state (possible CSRF)")

    tokens = await exchange_code_for_tokens(code)
    google_access_token = tokens.get("access_token")
    if not google_access_token:
        raise UnauthorizedError("Google did not return an access token")

    profile = await fetch_google_userinfo(google_access_token)
    google_id = profile.get("id")
    email = profile.get("email")
    if not google_id or not email:
        raise UnauthorizedError("Google profile is missing required fields")

    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            google_id=google_id,
            full_name=profile.get("name"),
            avatar_url=profile.get("picture"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif not user.google_id:
        user.google_id = google_id
        user.avatar_url = user.avatar_url or profile.get("picture")
        db.add(user)
        db.commit()
        db.refresh(user)

    token_pair = _issue_tokens(db, user)
    redirect_url = (
        f"{settings.FRONTEND_URL}/auth/callback"
        f"?access_token={token_pair.access_token}&refresh_token={token_pair.refresh_token}"
    )
    response = RedirectResponse(url=redirect_url)
    response.delete_cookie(STATE_COOKIE_NAME)
    return response


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the authenticated user's profile."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Update the authenticated user's own profile."""
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user
