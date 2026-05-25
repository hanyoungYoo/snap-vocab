from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from api.db import acquire
from api.settings import settings

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, key: str = ""):
    if key != settings.api_secret_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)

    async with acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM cards")
        due_today = await conn.fetchval(
            "SELECT COUNT(*) FROM cards WHERE next_review <= CURRENT_DATE"
        )
        accuracy_7d = await conn.fetchval(
            """SELECT COALESCE(AVG(correct::int)::float, 0)
               FROM review_logs WHERE reviewed_at >= NOW() - INTERVAL '7 days'"""
        )
        levels = await conn.fetch(
            "SELECT level, COUNT(*) AS n FROM cards GROUP BY level ORDER BY level"
        )

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "key": key,
            "total": total,
            "due_today": due_today,
            "accuracy_7d": round((accuracy_7d or 0) * 100, 1),
            "levels": [dict(r) for r in levels],
        },
    )
