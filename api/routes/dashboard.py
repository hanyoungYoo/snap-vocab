from fastapi import APIRouter, HTTPException, status

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
async def dashboard() -> dict:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "implemented in STEP 06")
