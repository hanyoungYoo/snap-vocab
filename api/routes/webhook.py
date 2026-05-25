from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/api", tags=["webhook"])


@router.post("/webhook/telegram")
async def telegram_webhook() -> dict:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "implemented in STEP 04")
