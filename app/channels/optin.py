"""Opt-in landing page (draft — Package H).

The other half of app.channels.email.send_initial_contact_email: a public,
no-auth page a counterparty reaches from that email. Clicking through to
WhatsApp (not merely visiting this page) is what actually satisfies
app.channels.whatsapp._has_valid_opt_in — see there for why. Visiting this
page is still recorded as an OptIn audit row, just not treated as consent
on its own.
"""

import uuid
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Case, ChannelEnum, OptIn, OptInMethodEnum

router = APIRouter(prefix="/optin", tags=["optin"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "public" / "templates"))


def _whatsapp_link(case: Case) -> str:
    settings = get_settings()
    text = quote(f"Merhaba, kiracınız adına DecisionOS'tan yazıyoruz — vaka {case.id}.")
    return f"https://wa.me/{settings.whatsapp_public_number}?text={text}"


@router.get("/{case_id}", response_class=HTMLResponse)
def optin_landing(case_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")

    db.add(
        OptIn(
            case_id=case.id,
            contact=case.counterparty_contact,
            channel=ChannelEnum.whatsapp,
            method=OptInMethodEnum.email_link_click,
        )
    )
    db.commit()

    return templates.TemplateResponse(
        request,
        "optin.html",
        {"counterparty_name": case.counterparty_name, "whatsapp_link": _whatsapp_link(case)},
    )
