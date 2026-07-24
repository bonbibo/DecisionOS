import pytest

from app.models import Case, ChannelEnum, StateEnum


@pytest.fixture
def new_case() -> Case:
    """A fresh, unpersisted Case sitting in the initial 'discovery' state."""
    return Case(
        channel=ChannelEnum.whatsapp,
        counterparty_contact="+15555550123",
        counterparty_name="Test Counterparty",
        state=StateEnum.discovery,
    )
