"""Public, unauthenticated pages (draft — Package I).

Landing page + waitlist — the trust face and the demand signal in one
package. `app/channels/optin.py`'s opt-in landing page shares this same
`app/public/templates/` directory (a different route, same "public, no
auth, Jinja" shape).
"""

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import WaitlistSignup
from app.schemas import WaitlistRequest, WaitlistResponse

router = APIRouter(tags=["public"])
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@router.get("/", response_class=HTMLResponse)
def landing(request: Request):
    return templates.TemplateResponse(request, "landing.html", {})


@router.post("/waitlist", response_model=WaitlistResponse)
def join_waitlist(payload: WaitlistRequest, db: Session = Depends(get_db)) -> WaitlistSignup:
    """Upserts by email — resubmitting (e.g. with an updated phone/note)
    should never 409 "already on the list", it should just update it."""
    signup = db.execute(select(WaitlistSignup).where(WaitlistSignup.email == payload.email)).scalars().first()
    if signup is None:
        signup = WaitlistSignup(email=payload.email)
        db.add(signup)
    signup.phone = payload.phone
    signup.note = payload.note
    signup.source = payload.source
    db.commit()
    db.refresh(signup)
    return signup


@router.get("/waitlist/thanks", response_class=HTMLResponse)
def waitlist_thanks(request: Request):
    return templates.TemplateResponse(request, "waitlist_thanks.html", {})
