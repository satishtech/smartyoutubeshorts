"""Google OAuth 2.0 authorization-code flow helpers."""
import logging
import secrets
from urllib.parse import urlencode

import httpx

from app.config import settings
from app.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def generate_state() -> str:
    """Generate a random CSRF-protection state token."""
    return secrets.token_urlsafe(32)


def build_authorization_url(state: str) -> str:
    """Build the Google consent-screen URL for the given CSRF state."""
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(code: str) -> dict:
    """Exchange an authorization code for Google access/id tokens."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                },
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.error("Google token exchange failed: %s", exc)
            raise ExternalServiceError("Failed to exchange Google authorization code") from exc


async def fetch_google_userinfo(access_token: str) -> dict:
    """Fetch the authenticated user's Google profile."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(
                GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.error("Google userinfo fetch failed: %s", exc)
            raise ExternalServiceError("Failed to fetch Google user profile") from exc
