import hmac
from pathlib import Path

from fastapi import APIRouter, Cookie, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

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
    resp.set_cookie(_COOKIE_NAME, key, httponly=True, secure=True, samesite="strict")
    return resp


@router.post("/logout")
async def logout():
    resp = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    resp.delete_cookie(_COOKIE_NAME)
    return resp


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, api_key: str = Cookie(default="")):
    if not _valid_key(api_key):
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request, "dashboard.html", {})
