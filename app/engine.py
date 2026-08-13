"""Negotiation state machine (draft).

Lifecycle: discovery -> anchoring -> counter <-> concession -> close
Any non-terminal state may also move directly to ``close`` (deal reached,
or either side walks away).
"""

import enum
import re
import warnings
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.models import ActorEnum, Case, Message, MessageKindEnum, Offer, StateEnum, User
from app.vault import VaultReader, parse_frontmatter

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
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
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
    """Parse every playbook note directly under vault/01-Playbooks/ (excluding taktikler/).

    Deprecated: thin wrapper over app.vault.VaultReader, kept for backward
    compatibility. New code should read VaultReader().read_folder(...) directly.
    """
    warnings.warn(
        "load_playbooks() is deprecated; use app.vault.VaultReader instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    context = VaultReader(vault_dir).read_folder("01-Playbooks", recursive=False)
    playbooks = []
    for doc in context.documents:
        meta = doc.frontmatter or {}
        if "playbook_id" not in meta:
            continue
        playbooks.append(
            Playbook(
                playbook_id=meta["playbook_id"],
                dikey=meta["dikey"],
                durum=meta["durum"],
                guncelleme=str(meta.get("guncelleme", "")),
                body=doc.body,
                source_path=Path(vault_dir) / doc.path,
            )
        )
    return playbooks


def tactics_for_stage(tactics: list[Tactic], dikey: str, asama: StateEnum) -> list[Tactic]:
    """Active tactics matching a playbook vertical + negotiation stage, best success rate first."""
    matches = [t for t in tactics if t.is_active and t.dikey == dikey and t.asama is asama]
    return sorted(matches, key=lambda t: t.basari_orani, reverse=True)


_PROFILE_HEADING_RE = re.compile(r"^##\s+(\S+)\s+—\s+(.+)$", re.MULTILINE)


@dataclass
class CounterpartyProfile:
    """A counterparty archetype loaded from a vault/04-Karsi-Taraf/*.md note.

    Profile notes have no per-archetype frontmatter; each archetype is a
    ``## <id> — <name>`` section within the file (e.g. ``## A1 — Kurumsal
    yönetim şirketi``), used by the Analist subagent to classify the other
    side of a negotiation.
    """

    profile_id: str
    ad: str
    body: str
    source_path: Path


def load_profiles(vault_dir: Path | str = "vault") -> list[CounterpartyProfile]:
    """Parse counterparty archetype sections from vault/04-Karsi-Taraf/*.md.

    Deprecated: thin wrapper over app.vault.VaultReader, kept for backward
    compatibility. New code should read VaultReader().read_folder(...) directly.
    """
    warnings.warn(
        "load_profiles() is deprecated; use app.vault.VaultReader instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    context = VaultReader(vault_dir).read_folder("04-Karsi-Taraf", recursive=False)
    profiles = []
    for doc in context.documents:
        text = doc.body
        headings = list(_PROFILE_HEADING_RE.finditer(text))
        for i, heading in enumerate(headings):
            start = heading.end()
            end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
            profiles.append(
                CounterpartyProfile(
                    profile_id=heading.group(1),
                    ad=heading.group(2).strip(),
                    body=text[start:end].strip(),
                    source_path=Path(vault_dir) / doc.path,
                )
            )
    return profiles


@dataclass
class Retro:
    """A post-case retrospective loaded from a vault/03-Retros/*.md note."""

    retro_id: str
    case: str
    sonuc: str
    tasarruf: float
    tasarruf_para_birimi: str
    tur_sayisi: int
    sure_gun: int
    yazan: str
    guncelleme: str
    body: str
    source_path: Path


def load_retros(vault_dir: Path | str = "vault") -> list[Retro]:
    """Parse every retro note under vault/03-Retros/*.md."""
    retros_dir = Path(vault_dir) / "03-Retros"
    retros = []
    for path in sorted(retros_dir.glob("*.md")):
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        if "retro_id" not in meta:
            continue
        retros.append(
            Retro(
                retro_id=meta["retro_id"],
                case=str(meta.get("case", "")),
                sonuc=meta.get("sonuc", ""),
                tasarruf=float(meta.get("tasarruf", 0) or 0),
                tasarruf_para_birimi=meta.get("tasarruf_para_birimi", ""),
                tur_sayisi=int(meta.get("tur_sayisi", 0) or 0),
                sure_gun=int(meta.get("sure_gun", 0) or 0),
                yazan=meta.get("yazan", ""),
                guncelleme=str(meta.get("guncelleme", "")),
                body=body,
                source_path=path,
            )
        )
    return retros


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
    # Append via the collection (not `case=case` in the constructor) so the
    # save-update cascade picks up the new row reliably on the next flush.
    offer = Offer(
        actor=actor,
        round_number=round_number,
        price=price,
        currency=currency,
        terms=terms,
    )
    case.offers.append(offer)
    return offer


def record_message(
    case: Case | None,
    channel,
    direction,
    content: str,
    sender: str | None = None,
    raw_payload: dict | None = None,
    *,
    user: User | None = None,
    kind: MessageKindEnum = MessageKindEnum.negotiation,
) -> Message:
    """Create a new Message tied to `case` (negotiation) and/or `user` (intake).

    Caller is responsible for adding/committing the message via a session —
    appending to a relationship collection on an already session-persistent
    parent (`case.messages` / `user.messages`) cascades reliably, which is
    why both are set via `.append()` here rather than `Message(case=..., user=...)`.
    """
    message = Message(
        channel=channel,
        direction=direction,
        kind=kind,
        sender=sender,
        content=content,
        raw_payload=raw_payload,
    )
    if case is not None:
        case.messages.append(message)
    if user is not None:
        user.messages.append(message)
    return message
