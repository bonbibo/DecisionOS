"""Negotiation state machine (draft).

Lifecycle: discovery -> anchoring -> counter <-> concession -> close
Any non-terminal state may also move directly to ``close`` (deal reached,
or either side walks away).
"""

import enum
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

from app.models import ActorEnum, Case, Message, Offer, StateEnum

# Allowed target states for each current state.
TRANSITIONS: dict[StateEnum, set[StateEnum]] = {
    StateEnum.discovery: {StateEnum.anchoring, StateEnum.close},
    StateEnum.anchoring: {StateEnum.counter, StateEnum.close},
    StateEnum.counter: {StateEnum.concession, StateEnum.close},
    StateEnum.concession: {StateEnum.counter, StateEnum.close},
    StateEnum.close: set(),
}


class InvalidTransition(Exception):
    """Raised when a state transition is not allowed from the case's current state."""


class NegotiationEvent(str, enum.Enum):
    anchor_set = "anchor_set"
    counter_received = "counter_received"
    concession_made = "concession_made"
    deal_closed = "deal_closed"
    walked_away = "walked_away"


EVENT_TARGET_STATE: dict[NegotiationEvent, StateEnum] = {
    NegotiationEvent.anchor_set: StateEnum.anchoring,
    NegotiationEvent.counter_received: StateEnum.counter,
    NegotiationEvent.concession_made: StateEnum.concession,
    NegotiationEvent.deal_closed: StateEnum.close,
    NegotiationEvent.walked_away: StateEnum.close,
}


_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?\n)---\s*\n?(.*)", re.DOTALL)


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a vault note into its YAML frontmatter dict and markdown body."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    raw_meta, body = match.groups()
    meta = yaml.safe_load(raw_meta) or {}
    return meta, body.strip()


@dataclass
class Tactic:
    """A negotiation tactic loaded from a vault/01-Playbooks/taktikler/*.md note."""

    taktik_id: str
    ad: str
    dikey: str
    asama: StateEnum
    durum: str
    kullanilma_sayisi: int
    basari_sayisi: int
    basari_orani: float
    risk: str
    guncelleme: str
    body: str
    source_path: Path

    @property
    def is_active(self) -> bool:
        return self.durum == "aktif"


@dataclass
class Playbook:
    """A negotiation playbook loaded from a vault/01-Playbooks/*.md note."""

    playbook_id: str
    dikey: str
    durum: str
    guncelleme: str
    body: str
    source_path: Path


def load_tactics(vault_dir: Path | str = "vault") -> list[Tactic]:
    """Parse every tactic note under vault/01-Playbooks/taktikler/*.md."""
    taktikler_dir = Path(vault_dir) / "01-Playbooks" / "taktikler"
    tactics = []
    for path in sorted(taktikler_dir.glob("*.md")):
        meta, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
        if "taktik_id" not in meta:
            continue
        tactics.append(
            Tactic(
                taktik_id=meta["taktik_id"],
                ad=meta["ad"],
                dikey=meta["dikey"],
                asama=StateEnum(meta["asama"]),
                durum=meta["durum"],
                kullanilma_sayisi=int(meta.get("kullanilma_sayisi", 0)),
                basari_sayisi=int(meta.get("basari_sayisi", 0)),
                basari_orani=float(meta.get("basari_orani", 0.0)),
                risk=meta.get("risk", "dusuk"),
                guncelleme=str(meta.get("guncelleme", "")),
                body=body,
                source_path=path,
            )
        )
    return tactics


def load_playbooks(vault_dir: Path | str = "vault") -> list[Playbook]:
    """Parse every playbook note directly under vault/01-Playbooks/ (excluding taktikler/)."""
    playbooks_dir = Path(vault_dir) / "01-Playbooks"
    playbooks = []
    for path in sorted(playbooks_dir.glob("*.md")):
        meta, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
        if "playbook_id" not in meta:
            continue
        playbooks.append(
            Playbook(
                playbook_id=meta["playbook_id"],
                dikey=meta["dikey"],
                durum=meta["durum"],
                guncelleme=str(meta.get("guncelleme", "")),
                body=body,
                source_path=path,
            )
        )
    return playbooks


def tactics_for_stage(tactics: list[Tactic], dikey: str, asama: StateEnum) -> list[Tactic]:
    """Active tactics matching a playbook vertical + negotiation stage, best success rate first."""
    matches = [t for t in tactics if t.is_active and t.dikey == dikey and t.asama is asama]
    return sorted(matches, key=lambda t: t.basari_orani, reverse=True)


class NegotiationEngine:
    """Wraps a single Case and enforces valid state transitions on it."""

    def __init__(self, case: Case, tactics: list[Tactic] | None = None):
        self.case = case
        self.tactics = tactics or []

    def available_tactics(self) -> list[Tactic]:
        """Active tactics for this case's vertical at its current stage, ranked by success rate."""
        if not self.case.vertical:
            return []
        return tactics_for_stage(self.tactics, self.case.vertical, self.case.state)

    def can_transition(self, target: StateEnum) -> bool:
        return target in TRANSITIONS.get(self.case.state, set())

    def transition(self, target: StateEnum) -> Case:
        if not self.can_transition(target):
            raise InvalidTransition(
                f"Cannot move case {self.case.id} from '{self.case.state.value}' "
                f"to '{target.value}'"
            )
        self.case.state = target
        if target is StateEnum.close:
            self.case.closed_at = datetime.now(timezone.utc)
        return self.case

    def apply_event(self, event: NegotiationEvent) -> Case:
        return self.transition(EVENT_TARGET_STATE[event])

    # --- convenience wrappers mirroring the negotiation vocabulary ---

    def start_anchor(self) -> Case:
        """discovery -> anchoring: the opening offer has been placed."""
        return self.apply_event(NegotiationEvent.anchor_set)

    def receive_counter(self) -> Case:
        """anchoring/concession -> counter: the counterparty pushed back."""
        return self.apply_event(NegotiationEvent.counter_received)

    def make_concession(self) -> Case:
        """counter -> concession: we moved price/terms toward the counterparty."""
        return self.apply_event(NegotiationEvent.concession_made)

    def close_deal(self) -> Case:
        """counter/concession -> close: agreement reached."""
        return self.apply_event(NegotiationEvent.deal_closed)

    def walk_away(self) -> Case:
        """discovery/anchoring -> close: negotiation abandoned before a deal."""
        return self.apply_event(NegotiationEvent.walked_away)


def record_offer(
    case: Case,
    actor: ActorEnum,
    price: float,
    currency: str = "USD",
    terms: str | None = None,
) -> Offer:
    """Append a new Offer to the case, auto-incrementing the round number.

    Caller is responsible for adding/committing the offer via a session.
    """
    round_number = max((o.round_number for o in case.offers), default=0) + 1
    offer = Offer(
        case=case,
        actor=actor,
        round_number=round_number,
        price=price,
        currency=currency,
        terms=terms,
    )
    case.offers.append(offer)
    return offer


def record_message(
    case: Case,
    channel,
    direction,
    content: str,
    sender: str | None = None,
    raw_payload: dict | None = None,
) -> Message:
    """Append a new Message to the case's transcript.

    Caller is responsible for adding/committing the message via a session.
    """
    message = Message(
        case=case,
        channel=channel,
        direction=direction,
        sender=sender,
        content=content,
        raw_payload=raw_payload,
    )
    case.messages.append(message)
    return message
