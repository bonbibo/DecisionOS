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
                          OutboundQueueItem, LoginCode, StateEnum + related enums
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
    whatsapp.py          Meta Cloud API webhook — routes to intake or run_turn(); opt-in guard
    email.py              Gmail send + initial-contact email (Package H)
    web.py                 POST /web/auth/request-code|verify-code|chat, GET /web/cases|case/{id}/timeline
    optin.py                GET /optin/{case_id} — click-to-WhatsApp landing page
  admin/
    __init__.py            /admin operator panel (Basic auth via REVIEW_TOKEN)
    templates/              Jinja templates for the panel
  intel/
    __init__.py             Listing dataclass, Adapter protocol
    property_finder.py       PropertyFinderAdapter (stub fetch, injectable fetch_fn)
    bayut.py                  BayutAdapter (same shape)
    aggregate.py               run_intel() -> vault/09-Piyasa-Verisi/<dikey>.md
  payments.py              Stripe pre-auth -> capture (Package G)
  public/
    __init__.py             GET /, POST /waitlist, GET /waitlist/thanks
    templates/               Shared with app/channels/optin.py
  portal/
    __init__.py             Customer portal pages (Portal L3): GET /portal/login|""|case/{id}
    templates/               Jinja shells; auth + data fetched client-side via app.channels.web's JSON API
  auth.py                   Email OTP login codes (LoginCode lifecycle) — see app.channels.web, app.portal
  health.py                Deep healthcheck (DB/vault/Stripe) — Package J
  logging_utils.py          JSON logging + request-id middleware — Package J
  reports.py                Daily ops report aggregation — Package J
alembic/                 Migrations (env.py wired to app.models metadata)
vault/                   Obsidian vault: playbooks + tactics (see below)
scripts/
  update_metrics.py        Regenerates vault/05-Metrikler/dashboard.md
  run_intel.py               Regenerates vault/09-Piyasa-Verisi/*.md (daily cron)
  daily_report.py             Writes reports/YYYY-MM-DD.md (+ emails OPS_EMAIL)
docs/
  RUNBOOK.md                Deploy/rollback/incident-response reference
  PROGRESS.md                MASTER-SPEC-v3 (F-K) final report — İNSAN GEREKLİ list, setup order
tests/                   pytest suite (state machine, VaultReader + legacy vault
                            loaders, subagents, orchestrator, LLM client, intake,
                            webhook + review flow, web channel + admin panel, market intel)
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
  09-Piyasa-Verisi/           generated (not hand-edited) — see scripts/run_intel.py
    kira-bae.md                comparable-listings summary for Stratejist's INTEL
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

### Market intel (`app/intel/`, `vault/09-Piyasa-Verisi/`)

`vault/09-Piyasa-Verisi/<dikey>.md` is the third "system-generated, not
hand-edited" vault folder (alongside `05-Metrikler/dashboard.md`) — a
per-vertical comparable-listings summary that rides along in Stratejist's
`INTEL` payload key automatically, no caller change required:

```bash
python scripts/run_intel.py   # regenerates every active vertical's note
```

- `app/intel/property_finder.py` / `app/intel/bayut.py`: each adapter's real
  fetch (Crawlee + the Playwright already provisioned in this environment)
  is a documented stub — the live CSS selectors were never verified against
  the real sites (see `docs/MASTER-SPEC-v3.md` Package F). Both adapters take
  an injectable `fetch_fn` (same seam pattern as
  `AnthropicSubagentClient(client=...)`), which is what tests and any real
  integration use; the default stub logs a warning and returns no listings
  rather than guessing at selectors that could silently scrape garbage or
  break ToS.
- `app/intel/aggregate.py::run_intel()`: for every vault/07-Fiyatlama/*.md
  vertical with `durum: aktif`, gathers listings from both adapters,
  computes `ortalama/min/max kira` + `ilan_sayisi`, and writes
  `vault/09-Piyasa-Verisi/<dikey>.md`. A run that finds no listings (e.g.
  the stub) **skips writing** rather than zeroing out a previously-good
  note — see `_aggregate`'s `None` return.
- `app.orchestrator._get_intel(case, vault_dir)` (mirrored in
  `app.intake._get_intel` for the intake-confirmation Stratejist call) reads
  the active note for the case's vertical and returns its frontmatter, or
  `{}` if there isn't one yet. `run_turn`'s `intel` parameter still exists
  as an explicit override (mainly for tests); its default (`None`) now means
  "look it up from the vault" instead of always `{}`.
- Intended to run daily via a Railway cron job — not wired up in this repo
  (deploy-platform config, not code); see `docs/PROGRESS.md`.

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
- **Dataset**: the same row also carries `request_payload` (the exact dict
  sent — `PLAN`/`DRAFT`/`VAULT`/`HUMAN_GUIDANCE`/etc., whatever that role's
  contract is) and `response_text` (the raw completion, before fence-
  stripping). Every subagent call the system ever makes is a complete,
  replayable input/output pair in `llm_calls` — not just its token count —
  so the full history (Analist's read of the counterparty, Stratejist's
  plan, Yazıcı's drafts, Kritik's verdicts, every escalation and the
  operator's answer) is queryable and exportable later for analysis or
  fine-tuning without having re-instrumented anything. `/admin/costs`
  reads the token/latency side of this; the payload/response columns are
  there for a future export script rather than surfaced in the UI yet.

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

### Human-in-the-loop question/answer (escalation)

Kritik's checklist item 7 (legal topic, phone number requested, aggression,
identity questions) and a handful of other conditions (max REVISE/REJECT
rounds exhausted, an unparseable subagent response after retry) return
`ESCALATE` — the negotiation stops rather than guessing, `Case.escalated`
flips `True`, and `Case.escalation_reason` carries Kritik's `violations` (or
the failure reason) as the question a human needs to look at. This was a
deliberate choice not to add new escalation triggers beyond what Kritik/the
retry logic already decide — Kritik's own checklist already knows what's
critical enough to stop for.

`app.orchestrator.resume_after_escalation()` is how an operator's answer
gets back in:

```python
# case.escalated is True, case.escalation_context["incoming_message"] holds
# the message that triggered it (set by _escalate at the moment it happened)
result = resume_after_escalation(case, client, "Bu normal, paylaşabilirsin", thread, tactics)
```

It re-runs the same turn (`run_turn` under the hood) with the answer
attached as `HUMAN_GUIDANCE` on *every* subagent call for that turn
(Analist/Stratejist/Yazıcı/Kritik all read it — each prompt has a short note
on what to do with it, e.g. Kritik: don't re-`ESCALATE` the same violation
if the operator already cleared it). Every answer is also appended to
`case.escalation_context["human_answers"]` (`{answer, answered_by,
answered_at}`) — a durable audit trail of the human side of the loop, kept
on the `Case` row itself rather than only in a log line.

Two front doors, same underlying function:
- `POST /review/case/{id}/answer` — `{answer, reviewed_by}`, same
  `Authorization: Bearer <REVIEW_TOKEN>` as the rest of `/review/*`. Returns
  the updated `CaseRead` (still escalated, or resolved).
- `/admin/cases/{id}` — a form shown whenever the case is escalated
  (`POST /admin/cases/{id}/answer`), same duplication-over-refactor pattern
  as the approve/edit/reject actions.

Either way, the queueing afterwards is identical to a normal WhatsApp turn:
an approved draft goes to `outbound_queue` (`audience=counterparty`); a
status update for the case's own user is queued too regardless of outcome
(still escalated, or resolved) — there's no synchronous requester to answer
inline here, unlike `POST /web/chat`.

## Payments (`app/payments.py`)

Closes `docs/MASTER-SPEC-v3.md` Package G: a card is pre-authorized (held,
never charged) when a case opens; the actual success fee is captured only
once the case closes `won` — never on `walked`, where the hold is released
instead. Same injectable-client seam as `AnthropicSubagentClient`: every
function takes an optional `stripe_client` (a `StripeClient` Protocol),
defaulting to `RealStripeClient()`.

- **Pre-auth at case open.** `app.intake._confirm_and_create_case` looks up
  the case's vertical pricing and, if priced, calls
  `create_pre_auth(case, pricing)` — amount is vault pricing's `min_ucret`
  (a floor, not the eventual fee — see below), attached via
  `case.payment = payment` (no `db` needed, same "caller persists" contract
  as `record_offer`/`record_message`). The case-created reply carries a
  checkout link (`GET /payments/checkout/{access_token}`, public/no-auth —
  the token itself is the credential); visiting it creates the actual
  Stripe Checkout Session on first click and redirects there.
- **`POST /payments/webhook`** verifies `Stripe-Signature` against
  `STRIPE_WEBHOOK_SECRET` — the same pattern as WhatsApp's
  `X-Hub-Signature-256` check. `checkout.session.completed` flips the
  `Payment` to `pre_authorized`; `payment_intent.payment_failed` to
  `failed`.
- **Capture/cancel on close.** `app.orchestrator._apply_recommended_state`
  now also sets `Case.outcome` (`won` on Analist's `"close"`, `walked` on
  `"walk"`) — the same signal that already drives the state transition.
  `app.payments.handle_turn_outcome(case)` is called right after every
  `run_turn`/`resume_after_escalation` (in `whatsapp.py`, `web.py`, and
  `review.py`'s `answer_escalation`) and captures or cancels the pre-auth
  the instant a case actually closes; a no-op otherwise.
- **Fee computation** (`compute_success_fee`): `savings = max(0, initial
  ask − final price)`, `fee = max(min_ucret, savings × basari_yuzdesi /
  100)` — `initial ask` is the counterparty's first recorded `Offer` (or
  the very first offer at all if the counterparty never stated one),
  `final price` the most recently recorded one by either side. This is why
  `Case`/`Yazıcı` offers are now actually recorded: `run_turn` calls
  `record_offer` whenever Analist's `counter_offer` or an approved draft's
  `offer_made` is a number — the `Offer` table existed since V1 but nothing
  wrote to it until this package needed real numbers to compute a fee from.
- **V1 simplification, explicitly signed off on**: the pre-auth amount
  (`min_ucret`) is a floor, not a ceiling — if the computed fee at capture
  time exceeds it, capture is capped at the pre-authorized hold and
  `Payment.note` records the shortfall for a manual follow-up charge (out
  of scope for V1 code).
- **The money-side guard**: `require_pre_auth(case)` — called from
  `review.py`/`admin`'s `approve()` for `audience=counterparty` sends on
  priced, non-demo cases — `409`s if the case's `Payment` hasn't reached at
  least `pre_authorized`. Same shape as Package H's opt-in guard: a real
  precondition enforced at the one place a message can actually go out.
- `/admin/payments` lists every `Payment`; case detail shows status +
  manual **Tahsil Et / İptal Et** overrides for when the automatic hook
  misses an edge case.

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
  - **Opt-in guard (Package H).** `send_text_message` now requires a `db`
    session and checks `_has_valid_opt_in` before it will send *anything* —
    unconditionally, not just for counterparty-audience messages, so there
    is exactly one choke point where a WhatsApp message can leave the
    system at all, and it's the same check every time. The only thing that
    counts as opt-in: an inbound WhatsApp `Message` from that recipient
    within the last 24h (Meta's own service-window rule) — visiting the
    `/optin/{case_id}` landing page is recorded as an `OptIn` audit row but
    does **not** satisfy the guard on its own; only the recipient actually
    messaging first does. No opt-in -> `OptInRequiredError` ->
    `POST /review/{id}/approve` and the `/admin` equivalent both turn that
    into a `409`.
- **Email** (`app/channels/email.py`): the Gmail send path
  (`send_email`) is real; inbound sync (`_sync_new_messages`,
  `POST /channels/email/webhook`) is still a stub — dispatch into `run_turn`
  is left as follow-up work once there's a reason to negotiate over email
  itself, not just use it for first contact (below).
  - **Email-first initial contact (Package H).** A cold WhatsApp message to
    a counterparty who has never talked to us risks Meta's opt-in policy
    (and the guard above would block it anyway). `send_initial_contact_email
    (case)` — called right after case creation in both
    `app.channels.whatsapp` and `app.channels.web` whenever
    `Case.counterparty_email` is known (an optional field the Intake
    subagent may collect, `ev_sahibi_email`) — sends a short templated
    email instead, with a link to `GET /optin/{case_id}` (public, no auth —
    a Jinja landing page under `app/public/templates/`). That page's
    **"WhatsApp'ta devam et"** button is a `https://wa.me/<WHATSAPP_PUBLIC_
    NUMBER>` click-to-WhatsApp link — if the counterparty clicks it and
    messages us, *they* initiated the WhatsApp conversation, which is
    real, Meta-compliant opt-in (and is exactly what the guard above
    checks for) rather than something this system claims on their behalf.
    A no-op when there's no `counterparty_email` — most cases still start
    on WhatsApp directly via an approved `outbound_queue` item once opted
    in some other way (e.g. `manual_operator`).
- **Web** (`app/channels/web.py`): our own customers talking to the agent
  directly through a browser instead of WhatsApp, with a synchronous
  request/response shape instead of a webhook:
  - `POST /web/auth/request-code` — `{email, phone, name}` -> creates (or,
    for a phone that already exists, e.g. from a prior WhatsApp contact,
    reuses) a `User`, then emails a 6-digit one-time code to `email`
    (`app.auth.create_login_code` + `app.channels.email.send_login_code_email`
    — see Portal login below). Never returns a token itself.
  - `POST /web/auth/verify-code` — `{email, code}` -> `app.auth.
    verify_login_code`; on success issues a bearer `session_token`
    (`User.web_session_token`, random 32-byte URL-safe token). Replaces the
    old "register with phone, no verification" trust model: holding a
    session token now requires having actually received the code at the
    email on file, not just knowing a phone number.
  - `GET /web/cases` — `Authorization: Bearer <session_token>`, lists the
    caller's own `Case`s (newest first) for the portal dashboard.
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

## Customer portal (`app/portal/`)

Server-rendered Jinja pages for customers to log in and see their own
cases — no build step, same "plain HTML + inline `<script>`" shape as
`app/public/`/`app/admin/`. The pages themselves carry no case data and no
server-side auth check; each page's script holds the bearer
`session_token` in `localStorage` and drives `app/channels/web.py`'s JSON
API directly, redirecting to `/portal/login` on any `401`.

- `GET /portal/login` — two-step form: email+phone+name ->
  `POST /web/auth/request-code`, then the 6-digit code ->
  `POST /web/auth/verify-code`. On success stores `session_token` in
  `localStorage` and redirects to `/portal`.
- `GET /portal` — dashboard: fetches `GET /web/cases`, renders each as a
  card linking to its detail page.
- `GET /portal/case/{id}` — fetches `GET /web/case/{id}/timeline`, renders
  `state`/`escalation_reason` plus the message log. The message-send box
  (posts to `POST /web/chat`) is hidden once `state == "close"`: `/web/
  chat` always routes to the caller's one active case (see above), so
  messaging from a closed case's page would silently land in the intake
  flow instead — the UI hides that trap rather than let it happen.

Free-text/counterparty-sourced fields (`counterparty_name`,
`item_description`, message `content`, `escalation_reason`) are run
through a small `dosEscape()` helper before being placed in `innerHTML` —
these values did not originate from us, so they're not trusted HTML.

## Landing + waitlist (`app/public/`)

Closes `docs/MASTER-SPEC-v3.md` Package I: the trust face and the demand
signal in one small, public (no-auth) package — plain HTML/CSS, one inline
`<script>` for the waitlist form's fetch call, no build step.

- `GET /` — the landing page (`app/public/templates/landing.html`):
  positioning pulled straight from `docs/product-one-pager.md` ("kazandırmazsak
  ödemezsiniz"), a 3-step how-it-works, and the waitlist form.
- `POST /waitlist` — `{email, phone?, note?, source?}` -> upserts a
  `WaitlistSignup` by `email` (resubmitting updates the row, never `409`s
  as "already on the list" — the point is to capture the latest signal,
  not gatekeep repeat visits).
- `GET /waitlist/thanks` — plain confirmation page.
- `/admin/waitlist` — list view (email/phone/note/source/date), same
  `REVIEW_TOKEN` Basic auth as the rest of `/admin`.

`app/channels/optin.py`'s opt-in landing page (Package H) shares this same
`app/public/templates/` directory — same "public, no auth, Jinja" shape,
different route.

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

## Üretim (`app/health.py`, `app/logging_utils.py`, `app/reports.py`)

Closes `docs/MASTER-SPEC-v3.md` Package J.

- **Structured logging**: every log line is one JSON object
  (`time`/`level`/`logger`/`message`/`request_id`) — `app.logging_utils.
  configure_logging()` replaces `logging.basicConfig`. `RequestIdMiddleware`
  reads (or generates) `X-Request-Id` per request, makes it available to
  every log line emitted while handling that request via a `ContextVar`
  (no explicit threading through call chains), and echoes it back in the
  response header — one request's full log trail is one grep away.
- **`GET /health/deep`**: DB connectivity (`SELECT 1`), vault manifest
  readability (`VaultReader.manifest_roles()`), and whether Stripe is
  configured (informational, doesn't affect `status`). `{"status": "ok"|
  "degraded", "checks": {...}}` — no auth (deploy platforms usually probe
  health endpoints without credentials). `GET /health` (existing, shallow)
  is unchanged.
- **`scripts/daily_report.py`**: writes `reports/YYYY-MM-DD.md` (git-
  ignored — deploy-environment artifact, not repo content) summarizing the
  previous day — new/closed (won vs. walked) cases, escalated cases
  (approximate — no dedicated escalation-event log yet, see
  `app.reports`' docstring), `llm_calls` volume, total captured payments,
  new waitlist signups. Emails it to `OPS_EMAIL` too if that's set (reuses
  the existing Gmail send path); file-only otherwise, never errors on a
  missing `OPS_EMAIL`. Intended to run daily via Railway cron, same as
  `scripts/run_intel.py`.
- **`docs/RUNBOOK.md`**: deploy steps, rollback, and incident-response
  notes for the failure modes this system actually has — Stripe webhook
  signature mismatches, WhatsApp signature mismatches, the opt-in guard or
  payment guard blocking a send unexpectedly (and why that's often
  correct, not a bug), an LLM outage (already routes to the human queue
  via `SubagentEscalated`, no extra code needed), migration issues.
- A regression test (`tests/test_ops.py::test_no_log_statement_references_
  a_secret_setting`) scans `app/**/*.py` for any `log*.*(...)` call whose
  arguments mention a secret `Settings` field name — guards against a
  future debug line accidentally logging a token/key.

## Ses kapısı (`vault/06-Kararlar/KR-003-ses-kanali-esigi.md`)

Closes `docs/MASTER-SPEC-v3.md` Package K — deliberately almost no code,
per the spec: the decision itself ("does voice/IVR investment make
sense yet?") stays a human call, `durum: taslak` in the vault; the only
code is what makes that decision *measurable*.

- `EscalationCategoryEnum` + `Case.escalation_category`: which Kritik
  checklist item (`app/prompts/kritik.md`, numbered 1-8) triggered the
  most recent `ESCALATE`, set by `app.orchestrator._categorize_escalation`
  in `_escalate()`. Parses Kritik's already-numbered `violations` text
  (`"<madde no>: <açıklama>"`) — checklist item numbers are never
  reassigned (`subagent-kontrati` skill), so this is stable to parse.
  Item 7 covers several distinct signals (phone/legal/aggression/
  identity) and isn't split (same reason); only the `"telefon"` substring
  within an item-7 violation maps to `phone_request`, everything else
  in item 7 falls into `escalation_signal_other`.
- `app.reports`' daily report gained a `phone_request_escalations` count
  + ratio — the exact number `KR-003` says to watch: **no voice-channel
  investment until `phone_request` exceeds 40% of total escalations.**
  The report makes the ratio visible; it doesn't act on it.
- **Also in this package** (bundled rather than a separate PR — see spec's
  "kapsam dışı" notes): `vault/06-Kararlar/KR-004-sirket-kimligi.md`
  (`durum: taslak`) records that the company/brand name is still an open
  decision, and `Settings.identity_name` (env `IDENTITY_NAME`) +
  `app.subagents.load_subagent_prompt`'s `{{IDENTITY_NAME}}` injection
  (`app/prompts/yazici.md`, `intake.md`) mean the code doesn't have to
  wait on that decision — it runs today with a placeholder name, and
  picking a real one is a config change, not a code change.

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

### MASTER-SPEC-v3 — F-K (waitlist -> capture)

`docs/MASTER-SPEC-v3.md` closes the gap from "working negotiation engine"
to "sellable product": market data feeding the engine, money actually
changing hands, a compliant way to reach a stranger, a public front door,
and the operational scaffolding a real deploy needs.

- **F — Market Intel.** `app/intel/` (Crawlee/Playwright-targeted
  adapters, real selectors still unverified — see the package's own
  "İNSAN GEREKLİ" note) aggregates comparable listings into
  `vault/09-Piyasa-Verisi/<dikey>.md` — the third "system-generated"
  vault folder, alongside `05-Metrikler/dashboard.md`. Stratejist's
  `INTEL` payload key is now auto-populated from it, no caller change.
- **G — Stripe pre-auth -> capture.** A card is held (never charged) at
  case open, captured only if the case closes `won` (`Case.outcome`, set
  from the same Analist signal that already drives the state machine),
  released if `walked`. `app.engine.record_offer` — built in V1 but never
  actually called — is now wired into `run_turn` so there's real offer
  history to compute the success fee from.
- **H — Email-first contact + opt-in guard.** `send_text_message` now
  refuses to send *anything* without a real inbound WhatsApp message from
  the recipient in the last 24h — one unconditional choke point, not a
  per-case judgment call. A counterparty we've never talked to gets an
  email with a click-to-WhatsApp link instead, so if a conversation
  starts, they started it.
- **I — Landing + waitlist.** `app/public/` — the trust face and the
  demand signal, plain HTML + one inline `<script>`, no build step.
- **J — Production hardening.** JSON structured logs + request-id
  correlation, `GET /health/deep`, a daily ops report
  (`scripts/daily_report.py`), `docs/RUNBOOK.md`.
- **K — Voice gate.** Almost no code on purpose: `KR-003` (vault, `durum:
  taslak`) is the actual decision; `Case.escalation_category` +
  the daily report's `phone_request` ratio are just what make that
  decision measurable instead of a guess.

Same rule as A-E: no negotiation-domain constant hardcoded in `app/`, and
test count only ever grew (146 at the start of F -> 229 after K).

## Status

Both specs (`SYSTEM UPDATE v2`, PR-A..E, and `MASTER-SPEC-v3`, Package
F..K) are implemented end to end: models, migrations, the state machine,
the vault-driven engine (pricing, decisions, segments, market intel), the
5-subagent orchestration loop with a real human-in-the-loop question/
answer path on every `ESCALATE`, a real Anthropic-backed `SubagentClient`
with full request/response dataset logging, WhatsApp + web
intake-or-negotiation routing with a real opt-in guard and payment
pre-auth/capture, a public landing/waitlist, and production scaffolding
(structured logs, deep healthcheck, daily ops report, runbook). Every
inbound/write surface is authenticated or guarded (WhatsApp signature
verification, Stripe webhook signature verification, `REVIEW_TOKEN`
bearer/Basic auth on review + admin, web session tokens, the WhatsApp
opt-in guard, the payment pre-auth guard). Test count has never regressed
across either spec (98 -> 229).

Deliberately out of scope (per explicit user sign-off, `docs/MASTER-
SPEC-v3.md`'s "Kapsam dışı" section): the legal-consultation escalation
signal stays a plain `ESCALATE` (no dedicated legal flow); the company
name/identity is a pending decision (`KR-004`, `IDENTITY_NAME` env
placeholder in the meantime); and demand-validation conversations with
real customers are human work, not code.

Still open (see each package's "İNSAN GEREKLİ" note in the commit that
closed it, and the eventual `docs/PROGRESS.md`): live verification of the
Property Finder/Bayut selectors and Railway cron wiring (F), a real Stripe
account + webhook registration (G), `WHATSAPP_PUBLIC_NUMBER` + Gmail OAuth
env values and a live click-to-WhatsApp check (H), real domain/DNS (I), a
real log aggregator/alerting integration (J, not requested by the spec),
and an actual dataset *export* (JSONL/fine-tuning format) on top of the
`llm_calls` storage — the data's there, nothing reads it out yet beyond
`/admin/costs`' token/latency rollup. The Gmail channel's inbound sync
(`_sync_new_messages`) and dispatch into `run_turn` also remain a stub —
email is used one-way (initial contact, reports) so far, never negotiated
over directly.
