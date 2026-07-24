"""Negotiation state machine (draft).

Lifecycle: discovery -> anchoring -> counter <-> concession -> close
Any non-terminal state may also move directly to ``close`` (deal reached,
or either side walks away).
"""

import enum
from datetime import datetime, timezone

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


class NegotiationEngine:
    """Wraps a single Case and enforces valid state transitions on it."""

    def __init__(self, case: Case):
        self.case = case

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
