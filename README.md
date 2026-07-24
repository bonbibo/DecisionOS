# DecisionOS — Negotiation Agent Backend

FastAPI + PostgreSQL skeleton for an automated negotiation agent. It tracks
a negotiation `Case` through a small state machine (`discovery -> anchoring
-> counter <-> concession -> close`), stores the `Message`/`Offer`
transcript, and exposes stub channel adapters for WhatsApp (Meta Cloud API)
and Gmail so a real integration can be built on top.

## Project layout

```
app/
  main.py            FastAPI app, health check, minimal Case endpoints
  config.py           Settings (env vars / .env)
  database.py          SQLAlchemy engine/session, declarative Base
  models.py            Case, Message, Offer, StateEnum + related enums
  engine.py             NegotiationEngine: the state machine
  schemas.py            Pydantic request/response models
  channels/
    whatsapp.py          Meta Cloud API webhook (verify + inbound) stub
    email.py              Gmail API (send + Pub/Sub push) stub
alembic/                 Migrations (env.py wired to app.models metadata)
tests/                   pytest suite (state machine transitions)
```

## State machine

```
discovery --> anchoring --> counter <--> concession --> close
    \_____________\_____________\_____________/
                         (walk away / deal closed)
```

`app/engine.py` defines the allowed transitions as `TRANSITIONS: dict[StateEnum, set[StateEnum]]`
and enforces them through `NegotiationEngine.transition()`, raising
`InvalidTransition` on any illegal jump (e.g. `discovery -> counter`, or any
move out of the terminal `close` state). Convenience methods
(`start_anchor`, `receive_counter`, `make_concession`, `close_deal`,
`walk_away`) wrap the underlying `NegotiationEvent` dispatch.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env with your local DATABASE_URL and channel credentials
```

### Database

```bash
# create a local Postgres role/db matching .env.example
createuser decisionos --pwprompt --createdb
createdb decisionos --owner=decisionos

alembic upgrade head
```

### Run the API

```bash
uvicorn app.main:app --reload
```

- `GET /health` — liveness check
- `POST /cases` / `GET /cases/{id}` — minimal Case CRUD
- `GET|POST /channels/whatsapp/webhook` — Meta Cloud API webhook
- `POST /channels/email/webhook` — Gmail Pub/Sub push endpoint

### Tests

```bash
pytest
```

`tests/test_engine.py` covers the state machine transitions: the full
happy path (`discovery -> ... -> close`), the counter/concession loop,
walking away early, `close` being terminal, and rejecting illegal skips
(e.g. `discovery -> counter`).

## Migrations

Alembic's `env.py` reads `DATABASE_URL` from `app.config.Settings` (which in
turn reads `.env`), and its `target_metadata` points at `app.database.Base`,
so `alembic revision --autogenerate` picks up model changes automatically.

```bash
alembic revision --autogenerate -m "message"
alembic upgrade head
alembic downgrade -1
```

## Channel stubs

- **WhatsApp** (`app/channels/whatsapp.py`): Meta Cloud API webhook
  verification (`GET`) and inbound message handling (`POST`), plus a
  `send_text_message` helper for outbound replies via the Graph API.
  Inbound parsing currently just logs the message — wiring it into
  `NegotiationEngine` + a DB session is left as a `TODO`.
- **Email** (`app/channels/email.py`): Gmail API client built from an
  OAuth2 refresh token, a Pub/Sub push receiver (`POST /channels/email/webhook`)
  for `users.watch()` notifications, and a `send_email` helper. History
  syncing (`_sync_new_messages`) and dispatch into the engine are stubs.

## Status

This is a backend skeleton: models, migrations, the state machine, and
channel entry points are wired up, but inbound-message-to-engine dispatch,
authentication, and outbound message templating are intentionally left as
follow-up work.
