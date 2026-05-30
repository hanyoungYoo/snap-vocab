import hmac

from fastapi import Cookie, Header, HTTPException, status

from api.settings import settings


async def verify_api_key(
    x_api_key: str = Header(default=""),
    api_key: str = Cookie(default=""),
) -> None:
    candidate = x_api_key or api_key
    if not candidate or not hmac.compare_digest(candidate, settings.api_secret_key):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid API key")
