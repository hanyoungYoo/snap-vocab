import hmac

from fastapi import Header, HTTPException, status

from api.settings import settings


async def verify_api_key(x_api_key: str = Header(...)) -> None:
    if not hmac.compare_digest(x_api_key, settings.api_secret_key):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid API key")
