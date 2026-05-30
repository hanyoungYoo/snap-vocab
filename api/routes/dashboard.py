import hmac
from pathlib import Path

from fastapi import APIRouter, Cookie, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from api.db import acquire
from api.settings import settings

router = APIRouter(tags=["dashboard"])
_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"
templates = Jinja2Templates(directory=_TEMPLATES_DIR)

_COOKIE_NAME = "api_key"


def _valid_key(key: str) -> bool:
    return hmac.compare_digest(key, settings.api_secret_key)


@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request, error: bool = False):
    return templates.TemplateResponse(request, "login.html", {"error": error})


@router.post("/login")
async def login(key: str = Form("")):
    if not _valid_key(key):
        return RedirectResponse("/?error=1", status_code=status.HTTP_303_SEE_OTHER)
    resp = RedirectResponse("/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    resp.set_cookie(_COOKIE_NAME, key, httponly=True, samesite="strict")
    return resp


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, api_key: str = Cookie(default="")):
    if not _valid_key(api_key):
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)

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
            "total": total,
            "due_today": due_today,
            "accuracy_7d": round((accuracy_7d or 0) * 100, 1),
            "levels": [dict(r) for r in levels],
        },
    )
