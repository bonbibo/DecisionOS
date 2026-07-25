"""Customer-facing portal (Portal L3): server-rendered Jinja shells, same
"public, no build step" shape as app.public/app.admin. No page here is
itself authenticated — each page's inline <script> holds the bearer
session_token in localStorage and calls the existing JSON API
(app.channels.web: POST /web/auth/request-code|verify-code, GET /web/
cases, GET /web/case/{id}/timeline, POST /web/chat), redirecting to
/portal/login on a 401. The HTML itself carries no case data server-side.
"""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/portal", tags=["portal"])
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@router.get("/login", response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse(request, "login.html", {})


@router.get("", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", {})


@router.get("/case/{case_id}", response_class=HTMLResponse)
def case_detail(request: Request, case_id: str):
    return templates.TemplateResponse(request, "case_detail.html", {"case_id": case_id})
