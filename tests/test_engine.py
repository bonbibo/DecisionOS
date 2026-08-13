import pytest

from app.engine import InvalidTransition, NegotiationEngine
from app.models import StateEnum


def test_happy_path_discovery_to_close(new_case):
    engine = NegotiationEngine(new_case)

    assert new_case.state is StateEnum.discovery

    engine.start_anchor()
    assert new_case.state is StateEnum.anchoring

    engine.receive_counter()
    assert new_case.state is StateEnum.counter

    engine.make_concession()
    assert new_case.state is StateEnum.concession

    engine.close_deal()
    assert new_case.state is StateEnum.close
    assert new_case.closed_at is not None


def test_counter_concession_loop_can_repeat_before_closing(new_case):
    engine = NegotiationEngine(new_case)
    engine.start_anchor()
    engine.receive_counter()

    # Multiple rounds of back-and-forth before a deal is struck.
    engine.make_concession()
    engine.receive_counter()
    engine.make_concession()
    assert new_case.state is StateEnum.concession

    engine.close_deal()
    assert new_case.state is StateEnum.close


def test_walk_away_is_allowed_before_a_deal_is_reached(new_case):
    engine = NegotiationEngine(new_case)
    assert new_case.state is StateEnum.discovery

    engine.walk_away()
    assert new_case.state is StateEnum.close
    assert new_case.closed_at is not None


def test_close_is_a_terminal_state(new_case):
    engine = NegotiationEngine(new_case)
    engine.start_anchor()
    engine.receive_counter()
    engine.close_deal()
    assert new_case.state is StateEnum.close

    with pytest.raises(InvalidTransition):
        engine.start_anchor()

    # State must not have changed after the failed transition.
    assert new_case.state is StateEnum.close


def test_skipping_states_raises_invalid_transition(new_case):
    engine = NegotiationEngine(new_case)
    assert new_case.state is StateEnum.discovery

    with pytest.raises(InvalidTransition):
        engine.receive_counter()  # discovery -> counter is not a legal jump

    assert new_case.state is StateEnum.discovery
