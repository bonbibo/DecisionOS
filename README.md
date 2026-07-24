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
  models.py            User, UserMemory, Case, Message, Offer, LLMCall,
                          OutboundQueueItem, StateEnum + related enums
  vault.py               VaultReader: the single gateway onto vault/ (manifest-driven)
  engine.py             NegotiationEngine: the state machine + legacy vault loaders
  intake.py              5th subagent: onboarding conversation before a Case exists
  metrics.py             Dashboard generation from vault frontmatter
  subagents.py            Subagent prompt loading + JSON response contract
  orchestrator.py          Turn flow: Analist -> Stratejist -> Yazıcı <-> Kritik
  llm.py                   AnthropicSubagentClient (real LLM calls + cost logging)
  review.py                POST /review/{id}/approve|edit|reject (human-in-the-loop queue)
  schemas.py            Pydantic request/response models
  prompts/                 Subagent system prompts, incl. intake.md (see below)
  channels/
    whatsapp.py          Meta Cloud API webhook — routes to intake or run_turn()
    email.py              Gmail API (send + Pub/Sub push) stub
    web.py                 POST /web/register|chat, GET /web/case/{id}/timeline
  admin/
    __init__.py            /admin operator panel (Basic auth via REVIEW_TOKEN)
    templates/              Jinja templates for the panel
alembic/                 Migrations (env.py wired to app.models metadata)
vault/                   Obsidian vault: playbooks + tactics (see below)
scripts/
  update_metrics.py        Regenerates vault/05-Metrikler/dashboard.md
tests/                   pytest suite (state machine, VaultReader + legacy vault
                            loaders, subagents, orchestrator, LLM client, intake,
                            webhook + review flow, web channel + admin panel)
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
- `GET|POST /channels/whatsapp/webhook` — Meta Cloud API webhook (real dispatch, see below)
- `POST /channels/email/webhook` — Gmail Pub/Sub push endpoint
- `POST /review/{id}/approve|edit|reject` — human-in-the-loop outbound queue

### Tests

```bash
pytest
```

Most of the suite (state machine, vault loaders, subagents, orchestrator) is
pure Python and needs nothing running. `tests/test_llm.py`, `tests/test_intake.py`,
`tests/test_webhook_and_review.py`, `tests/test_intake_webhook.py`, and the
`db_session`/`api_client`/`make_case`/`make_user` fixtures in `tests/conftest.py`
exercise real DB persistence and need a reachable Postgres matching
`DATABASE_URL` — they never call the real Anthropic or Meta Graph APIs (the
LLM client and `send_text_message` are monkeypatched with fakes), so no API
keys are required either.

## Migrations

Alembic's `env.py` reads `DATABASE_URL` from `app.config.Settings` (which in
turn reads `.env`), and its `target_metadata` points at `app.database.Base`,
so `alembic revision --autogenerate` picks up model changes automatically.

```bash
alembic revision --autogenerate -m "message"
alembic upgrade head
alembic downgrade -1
```

## Vault-driven engine (`app/vault.py`)

Vault change = behavior change, no deploy: **`VaultReader` is the single
gateway** for reading `vault/` content — no subagent or module opens a vault
file directly. Which folders each role may see is declared in
`vault/_manifest.md` (`roles: {role: [folder, ...]}`), not hardcoded in
Python:

```python
from app.vault import VaultReader

context = VaultReader("vault").read_for_role("stratejist")
# context.documents: [VaultDocument(path, frontmatter: dict | None, body: str), ...]
# context.warnings: e.g. "unknown role", "manifest path not found" — never a crash
```

`app.orchestrator.run_turn` and `app.intake.run_intake_turn` call this before
*every* subagent request and attach the result as a `"VAULT"` key on that
role's payload — so a vault edit changes what the next turn's Stratejist/
Yazıcı/Kritik/Analist/Intake call sees, with no code change and no restart
(hot-reload: every call re-reads from disk, no caching in V1). Frontmatter'd
notes parse to a `dict`; frontmatter-less notes carry `frontmatter=None` and
the whole file as `body`. Document order is always path-sorted, for
consistent prompt-cache behavior across turns.

```
vault/
  _manifest.md               role -> folder mapping (edit this to add a folder for a role)
  01-Playbooks/
    kira-bae.md              playbook note (anchor strategy, concession ladder, red lines)
    taktikler/
      TK-001-*.md, TK-002-*.md, TK-003-*.md   tactic notes
  02-Cases/                  case log (filled in per case; empty for now)
  03-Retros/                 post-case retros (filled in by the Kütüphaneci agent per case)
  04-Karsi-Taraf/
    profiller.md              counterparty archetypes (## <id> — <name> sections, no frontmatter)
  05-Metrikler/
    dashboard.md               win-rate / tactic-score dashboard — regenerated, not hand-edited
  06-Kararlar/
    KR-001-fiyatlama-modeli.md   pricing model decision (durum: aktif)
    KR-002-dikey-sirasi.md       vertical rollout order decision (durum: aktif)
  07-Fiyatlama/
    kira-bae.md                pricing model (`durum: aktif`) — success fee % / min fee / flat alternative
    arac-bae.md                second-vertical demo pricing (`durum: demo`) — not offered to real customers
  08-Musteri-Profilleri/
    segmentler.md               customer segments (S1/S2/S3, no frontmatter — our own customer,
                                   not the counterparty; see 04-Karsi-Taraf for that)
  _sablonlar/                 templates for new tactic / retro notes
```

The system never writes back to the vault (except the already-generated
`05-Metrikler/dashboard.md`) — a Kütüphaneci-authored proposal file + human
merge is the only path for the vault to change.

`load_playbooks()`/`load_profiles()` in `app/engine.py` are now thin,
`DeprecationWarning`-emitting wrappers over `VaultReader` (kept for
call-site compatibility); `load_tactics()`/`load_retros()` still read
directly for now — natural follow-ups to migrate onto `VaultReader` too.

### Decisions (`06-Kararlar/`)

Architecture/product decisions are vault notes, not code comments — start
from `vault/_sablonlar/karar-sablonu.md` (`karar_id`, `durum`,
`etki_alani`, `gozden_gecirme` frontmatter). `stratejist` and `kritik` are
the two manifest roles scoped to `06-Kararlar/` (Kritik's checklist item 8:
does this draft contradict an active decision? → `REVISE`; Stratejist:
don't produce a plan contradicting one, flag any tension in `rationale`).
`VaultContext.exclude_inactive_decisions()` drops any `06-Kararlar/*.md`
note that isn't `durum: aktif` before it reaches a subagent payload — a
`taslak`/`iptal`/`gozden-gecirilecek` decision is vault history, not live
context. Every other folder is passed through untouched; this filter is
`06-Kararlar/`-specific, not a generic `durum` filter.

### Customer segments (`08-Musteri-Profilleri/`)

Not to be confused with `04-Karsi-Taraf/`'s A1/A2/A3 (the *counterparty*
archetypes) — `08-Musteri-Profilleri/segmentler.md`'s S1/S2/S3 describe
*our own customer* (new expat / established expat / corporate, each with
different negotiation calibration rules). `app/prompts/analist.md` is
explicit about not conflating the two, since Analist's manifest scope
includes both folders.

- Intake may write `memory_updates.segment` ("S1"/"S2"/"S3") once it's
  confident — never a guess; the prompt tells it to leave the key out
  entirely rather than write an uncertain segment.
- `app.orchestrator._get_segment(case)` / the equivalent inline lookup in
  `app.intake._confirm_and_create_case` reads `segment` back out of
  `UserMemory` and passes it to Stratejist as `SEGMENT` — `None` if the
  case has no linked user or the segment isn't known yet, in which case
  Stratejist is told not to assume one and plan from `CASE`/`PROFILE` alone.

Each tactic note has YAML frontmatter (`taktik_id`, `dikey`, `asama`,
`durum`, `basari_orani`, `risk`, ...). `app/engine.py` parses these directly:

```python
from app.engine import load_tactics, load_playbooks, NegotiationEngine

tactics = load_tactics("vault")          # every vault/01-Playbooks/taktikler/*.md note
playbooks = load_playbooks("vault")      # every vault/01-Playbooks/*.md playbook note

engine = NegotiationEngine(case, tactics=tactics)
engine.available_tactics()               # active tactics matching case.vertical + case.state
```

`Case.vertical` (e.g. `"kira-bae"`) selects which playbook's tactics apply;
`available_tactics()` filters the loaded tactics to the case's current
negotiation stage (`discovery`/`anchoring`/`counter`/`concession`/`close`)
and ranks them by `basari_orani` (success rate).

### Counterparty profiles

`load_profiles()` parses `vault/04-Karsi-Taraf/*.md` into `CounterpartyProfile`
records — one per `## <id> — <name>` section (these notes have no per-archetype
frontmatter). Intended for the Analist subagent's counterparty classification:

```python
from app.engine import load_profiles

for profile in load_profiles("vault"):
    print(profile.profile_id, profile.ad)   # e.g. "A1 Kurumsal yönetim şirketi"
```

### Metrics dashboard

`vault/05-Metrikler/dashboard.md` is generated, not hand-edited. It's derived
from `vault/03-Retros/*.md` frontmatter (case outcomes, savings, round counts)
and `vault/01-Playbooks/taktikler/*.md` frontmatter (per-tactic usage/success
counts). After the Kütüphaneci agent files a retro or updates a tactic's
score, regenerate it with:

```bash
python scripts/update_metrics.py
```

## Subagents (Stratejist / Yazıcı / Kritik / Analist / Intake)

`app/prompts/*.md` holds each subagent's full system prompt as plain
Markdown — a prompt update is a `git push`, not a code change (`app/prompts/README.md`
documents the flow in detail). `app/subagents.py` loads them and enforces
the JSON-only response contract every subagent is bound to:

```python
from app.subagents import SubagentRole, call_subagent_json

# `client` implements SubagentClient.complete(role, system_prompt, payload) -> str
data = call_subagent_json(client, SubagentRole.analist, {"INCOMING": "...", ...})
```

A response that isn't valid JSON, or is missing required keys for that role,
gets one retry; if it's still bad, `call_subagent_json` raises
`SubagentEscalated` — the caller's cue to hand off to a human.

`app/orchestrator.run_turn(case, client, incoming_message, thread, tactics, ...)`
wires the full per-message flow:

```
Analist(JSON) -> apply recommended_state to the case
-> Stratejist (only if case.plan is empty, or after a Kritik REJECT)
-> Yazıcı(draft) <-> Kritik(verdict)
     APPROVE  -> TurnResult(status="approved", draft=...)
     REVISE   -> back to Yazıcı with a revision_note (max 2 rounds)
     REJECT   -> re-plan with Stratejist (max 1 replan), then retry
     ESCALATE -> stop immediately
```

Any escalation (bad JSON, an illegal state jump, exhausted REVISE/REJECT
budget, or an explicit Kritik `ESCALATE`) sets `case.escalated = True` and
`case.escalation_reason`, for a human-in-the-loop queue to pick up.

`SubagentClient` is a `Protocol`; `app/llm.py`'s `AnthropicSubagentClient` is
the real implementation (see below). Tests exercise the full orchestration
loop against a scripted fake client instead (`tests/test_orchestrator.py`),
so none of that requires an API key to run.

## LLM client (`app/llm.py`)

`AnthropicSubagentClient` implements `SubagentClient` against the real
Anthropic Messages API. One instance is bound to a `case_id` and/or `user_id`
+ DB session (construct it per turn) so every call it makes can be logged.
`case_id` is `None` for intake calls, which happen before any Case exists:

```python
from app.llm import AnthropicSubagentClient

# negotiation turn
client = AnthropicSubagentClient(case_id=case.id, db=db, user_id=case.user_id)
run_turn(case, client, incoming_message=text, thread=thread, tactics=tactics)

# intake turn (no case yet)
client = AnthropicSubagentClient(case_id=None, db=db, user_id=user.id)
run_intake_turn(user, client, incoming_message=text, thread=thread, tactics=tactics)
```

- **Model per role** comes from `Settings` (`MODEL_YAZICI`, `MODEL_STRATEJIST`,
  `MODEL_ANALIST`, `MODEL_KRITIK`, `MODEL_INTAKE` in `.env`) — not hardcoded, so
  a model swap is a config change. `.env.example`'s defaults follow
  `app/prompts/README.md`'s suggestion (Sonnet for Stratejist/Yazıcı/Intake,
  Haiku for Analist/Kritik); confirm against real `llm_calls` cost/quality data
  before trusting it long-term.
- **JSON enforcement**: the system prompt gets a `"SADECE geçerli JSON döndür."`
  suffix, and a leading/trailing ` ```json ... ``` ` fence is stripped from the
  response before it reaches `app.subagents.call_subagent_json`'s existing
  parse-validate-retry-then-escalate logic — nothing about that retry
  mechanism changed.
- **Cost tracking**: every call logs a row to `llm_calls` (`case_id`, `user_id`,
  `role`, `model`, `input_tokens`, `output_tokens`, `latency_ms`), so a per-role
  cost/quality query against real traffic is just a SQL query away.

## Intake & user memory (`app/intake.py`)

Before a `Case` exists, a new WhatsApp number is a prospective customer, not
a negotiation counterparty — `app/prompts/intake.md` is a 5th subagent that
onboards them:

```python
from app.intake import run_intake_turn

result = run_intake_turn(user, client, incoming_message=text, thread=thread, tactics=tactics)
# result.status: "reply" | "case_created" | "escalated"
```

- Each turn's JSON (`reply`, `collected_fields`, `missing_fields`, `ready`,
  optional `memory_updates`) is stored on `User.intake_state` and fed back in
  as `COLLECTED_FIELDS` on the next turn, so the brief accumulates across
  messages. `app/prompts/intake.md` defines the exact `collected_fields` keys
  (`hedef_kira`, `ev_sahibi_iletisim`, ... — edit that file, not code, to
  change the schema) and requires `hedef_kira` + `ev_sahibi_iletisim` before
  `ready` can flip `true`.
- Once `ready=true`, the subagent's own `reply` carries the savings-fee
  summary + approval ask, and `awaiting_confirmation` is set. The **next**
  message is checked with a simple deterministic keyword match
  (`evet`/`yes`/`onaylıyorum`/...) — not another LLM call — rather than
  inventing a `confirmed` field in the JSON contract. A confirmation creates
  the `Case` from `collected_fields`, calls Stratejist once to seed
  `Case.plan`, and moves the case straight to `anchoring` via
  `NegotiationEngine.start_anchor()`. Anything else falls through to a
  normal intake turn (corrections, questions, etc.).
- **No hardcoded fee numbers anywhere in code or prompts.** The `PRICING`
  input (`app/intake.py`'s `_select_pricing`) pulls the active
  `vault/07-Fiyatlama/<dikey>.md` frontmatter (`basari_yuzdesi`, `min_ucret`,
  `para_birimi`, `sabit_alternatif`) into every intake call; `durum: demo`
  pricing (e.g. `arac-bae.md`) is excluded unless explicitly requested with
  `allow_demo=True`, which intake never does — real customers only ever see
  `durum: aktif` pricing. When `ready=true`, the subagent must also return a
  `fee_offer` echoing those numbers back; `_fee_mismatch` compares it against
  `PRICING` and, on a mismatch, retries once with a `REVISION_NOTE` before
  escalating — protection against the LLM inventing or misremembering a fee.
- `memory_updates` are durable facts worth keeping across cases (e.g.
  `risk_toleransi: dusuk`) — written to `UserMemory` (unique per
  `(user_id, key)`, upserted) and fed back as `MEMORY` on every future intake
  turn for that user, in this case and any future one.
- Intake replies are **sent directly** via `whatsapp.send_text_message`, not
  queued in `outbound_queue` — this is a real-time onboarding chat with our
  own customer, a fundamentally lower-risk audience than the counterparty
  drafts the approval queue exists to gate. (This direct-send design wasn't
  explicitly specified in the intake task and is worth confirming matches
  the intended UX.)

## Review queue (`app/review.py`)

`run_turn` never sends anything by itself. When Kritik returns `APPROVE`,
the WhatsApp webhook writes the draft into `outbound_queue` with status
`pending_approval` and `audience=counterparty`; it also queues a short
bilingual status note for the case's own user (`audience=client`, same
`pending_approval` gate — see Channels below for why that one stays gated
too in V1). Actually sending only happens via:

- `POST /review/{id}/approve` — the only endpoint that actually sends: calls
  `whatsapp.send_text_message` and marks the item `sent` (currently
  WhatsApp-only; other channels 501 until wired).
- `POST /review/{id}/edit` — updates the draft's `message` text, status -> `edited`
  (still requires a follow-up `approve` to actually send).
- `POST /review/{id}/reject` — status -> `rejected`, never sent.

This is a deliberately simple V1: plain REST, no UI, but **not** unauthenticated
— every `/review/*` request requires `Authorization: Bearer <REVIEW_TOKEN>`
(set in `.env`; generate a real random value, e.g. `openssl rand -hex 32`,
before deploying). Anyone with the token can approve/send on the agent's
behalf, so treat it like any other credential. A future version could drive
the same three endpoints from a second WhatsApp bot number instead of a web
panel — the queue table doesn't care who calls it, as long as they have the token.

## Channels

- **WhatsApp** (`app/channels/whatsapp.py`): the webhook verification
  handshake (`GET`) is unchanged. The inbound handler (`POST`) first verifies
  Meta's `X-Hub-Signature-256` header — an HMAC-SHA256 of the raw request
  body keyed with `WHATSAPP_APP_SECRET` — and rejects with `401` if it's
  missing or doesn't match, so only Meta (or someone who has the app secret)
  can feed us events. Once verified, the sender's phone number routes the
  message one of two ways:
  - **Has an active (non-`close`) `Case` as its `counterparty_contact`** —
    negotiation. Append the message to `Case.messages`, build the last 10
    as `thread`, load fresh `tactics`/`profiles` from `vault/`, and run
    `app.orchestrator.run_turn`. An `APPROVE`d draft goes to `outbound_queue`
    (`audience=counterparty`); a short status note for the case's own user
    (if any) is queued too (`audience=client`) — kept `pending_approval` in
    V1 even though it doesn't carry negotiation risk, so there's a single
    send path to reason about rather than two.
  - **No active `Case` for that number** — intake. Routed to
    `app.intake.run_intake_turn` instead (see above); replies are sent
    directly, not queued.
  Nothing negotiation-facing is ever sent from inside the webhook handler
  itself — only `POST /review/{id}/approve` sends counterparty/client-status drafts.
- **Email** (`app/channels/email.py`): still a stub. Gmail API client built
  from an OAuth2 refresh token, a Pub/Sub push receiver
  (`POST /channels/email/webhook`) for `users.watch()` notifications, and a
  `send_email` helper. History syncing (`_sync_new_messages`) and dispatch
  into `run_turn` are left as follow-up work (mirroring the WhatsApp wiring
  above once there's an email vertical to test against).
- **Web** (`app/channels/web.py`): our own customers talking to the agent
  directly through a browser instead of WhatsApp, with a synchronous
  request/response shape instead of a webhook:
  - `POST /web/register` — `{email, phone, name}` -> creates (or, for a
    phone that already exists, e.g. from a prior WhatsApp contact, reuses)
    a `User` and issues a bearer `session_token`
    (`User.web_session_token`, random 32-byte URL-safe token). V1 has no
    email/phone verification, same trust model as WhatsApp: whoever holds
    the token is treated as that phone's owner.
  - `POST /web/chat` — `Authorization: Bearer <session_token>`, body
    `{message}`. Routing mirrors WhatsApp but keyed by the authenticated
    `User` instead of a phone number (`Case.user_id == user.id` and
    `state != close`, rather than matching `counterparty_contact`, since
    the web session identifies our customer, not the counterparty):
    active case -> `run_turn`; no active case -> `run_intake_turn`. The
    counterparty-facing draft (if `APPROVE`d) is still queued in
    `outbound_queue` (`audience=counterparty`, `channel=whatsapp` — the
    counterparty is only ever reached over WhatsApp, regardless of which
    channel our customer used) for the unchanged human-approval flow. The
    client-facing status update is **not** queued here: this channel is
    synchronous, so `app.orchestrator.status_message_for()` (the same
    helper WhatsApp queues as `audience=client`) is returned inline as the
    HTTP response's `reply` instead.
  - `GET /web/case/{id}/timeline` — same bearer auth; 404s if the case
    isn't the caller's own. Returns current `state`/`escalated` plus the
    case's `messages` and `offers` logs (there's no separate
    state-transition history table, so the timeline is reconstructed from
    those two logs rather than a dedicated audit trail).

## Operator panel (`app/admin/`)

A small server-rendered Jinja UI at `/admin` for the same human-in-the-loop
queue `app/review.py` exposes over REST — for a person who'd rather click
through a page than call the API by hand. Protected by HTTP Basic auth
checked against the same `REVIEW_TOKEN` (`/review/*` compares it as a
Bearer token; `/admin` compares it as the Basic password — same credential,
two auth schemes). It deliberately duplicates `review.py`'s small
approve/edit/reject state-transition logic rather than importing/refactoring
it, so `review.py`'s tested REST contract stays untouched.

- `/admin` — every `outbound_queue` item still `pending_approval`/`edited`,
  across all cases, with inline **Onayla & Gönder** / **Düzenle** /
  **Reddet** actions; escalated cases' rows are visually flagged.
  Approving here calls `whatsapp.send_text_message` directly, exactly like
  `POST /review/{id}/approve`.
- `/admin/cases`, `/admin/cases/{id}` — case list and a detail/timeline
  view (plan, messages, offers), escalated cases highlighted.
- `/admin/costs` — `llm_calls` usage rollups (call count, input/output
  tokens, average latency), grouped per case and per subagent role/model.
  No dollar figures are computed here — the codebase doesn't hardcode a
  $/token rate table, so this stays an honest token/latency view rather
  than a fabricated cost estimate.

## Öğrenme Mimarisi

This closes out the "Vault-Driven Decision Engine" system update (PR-A
through PR-E, landed as sequential commits on this branch/PR): the system's
negotiation knowledge — pricing, tactics, playbooks, architecture decisions,
customer segments — lives in `vault/` as editable notes, not hardcoded in
`app/`, and every subagent call reads that vault fresh through one gateway.

- **PR-A — `VaultReader` + `_manifest.md`.** One gateway (`app/vault.py`)
  onto all vault content; role -> folder scope is declared data
  (`vault/_manifest.md`), not a Python `if`. Hot-reload, no caching:
  editing a note changes the next turn's subagent payload with no deploy.
- **PR-B — Pricing (`07-Fiyatlama/`).** The engine validates the LLM's
  `fee_offer` against the vault's pricing frontmatter by exact comparison
  (`app.intake._fee_mismatch`) rather than trusting or regex-scraping the
  model's free text — one revision retry, then escalate on a persistent
  mismatch. `Case.is_demo` gates access to non-`aktif` (`demo`) pricing.
- **PR-C — Decisions (`06-Kararlar/`).** Architecture/product decisions are
  vault notes (ADR-style, `vault/_sablonlar/karar-sablonu.md`), which
  Stratejist and Kritik are scoped to read; `exclude_inactive_decisions()`
  keeps anything not `durum: aktif` out of subagent payloads automatically.
- **PR-D — Customer segments (`08-Musteri-Profilleri/`).** `SEGMENT`
  (S1/S2/S3, from `UserMemory`) rides alongside every Stratejist call,
  calibrating the plan to who our own customer is — kept deliberately
  distinct from `04-Karsi-Taraf`'s counterparty archetypes (A1/A2/A3),
  since Analist reads both and they answer different questions.
- **PR-E — Web channel + operator panel.** A second, synchronous customer
  channel (`app/channels/web.py`) reusing the same `run_turn`/
  `run_intake_turn` orchestration WhatsApp uses, plus a server-rendered
  `/admin` panel (`app/admin/`) over the same human-approval queue
  `app/review.py` exposes as REST — two front doors onto one engine, no
  duplicated negotiation logic.

No negotiation-domain constant (a fee percentage, a tactic, a segment
definition, a decision) is hardcoded in `app/` — every one of those is read
from `vault/` at call time. Test count has not regressed at any point across
PR-A through PR-E (98 -> 112 as tests were *added*, never removed to make a
change pass).

## Status

Models, migrations, the state machine, the vault-driven engine (pricing,
decisions, segments — see Öğrenme Mimarisi above), the subagent
orchestration loop (including intake/onboarding), a real Anthropic-backed
`SubagentClient` with cost logging, and the full WhatsApp + web
intake-or-negotiation routing -> human-approval -> send loop (via
`POST /review/*` or the `/admin` panel) are wired up end to end, with every
inbound/write surface authenticated (WhatsApp signature verification,
`REVIEW_TOKEN` bearer/Basic auth on review + admin, web session tokens).
Still open: the Gmail channel's `run_turn`/intake dispatch, multi-channel
sending in `POST /review/{id}/approve` (WhatsApp only today — a web-origin
case's counterparty draft is still queued as `channel=whatsapp`, since the
counterparty side has no web presence), and auth/identity on the intake
side (any WhatsApp number or `{email, phone}` pair can start a case —
reasonable for a public onboarding flow, but worth a deliberate look before
scaling pilots).
