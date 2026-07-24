import logging

from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.channels import email, whatsapp
from app.config import get_settings
from app.database import get_db
from app.models import Case
from app.schemas import CaseCreate, CaseRead

settings = get_settings()
logging.basicConfig(level=settings.log_level)

app = FastAPI(title="DecisionOS Negotiation Agent", version="0.1.0")

app.include_router(whatsapp.router)
app.include_router(email.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/cases", response_model=CaseRead, status_code=201)
def create_case(payload: CaseCreate, db: Session = Depends(get_db)) -> Case:
    case = Case(**payload.model_dump())
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@app.get("/cases/{case_id}", response_model=CaseRead)
def get_case(case_id: str, db: Session = Depends(get_db)) -> Case:
    case = db.execute(select(Case).where(Case.id == case_id)).scalar_one()
    return case
