import json

import pytest

from app.subagents import (
    SubagentEscalated,
    SubagentRole,
    call_subagent_json,
    load_subagent_prompt,
)


class ScriptedClient:
    """A fake SubagentClient that returns scripted raw responses in order."""

    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.call_count = 0

    def complete(self, role, system_prompt, payload):
        self.call_count += 1
        return self._responses.pop(0)


@pytest.mark.parametrize("role", list(SubagentRole))
def test_load_subagent_prompt_reads_real_files(role):
    prompt = load_subagent_prompt(role)
    assert prompt.strip()
    assert "SUBAGENT" in prompt


def test_call_subagent_json_parses_valid_response_on_first_try():
    client = ScriptedClient([json.dumps({"archetype": "A1", "recommended_state": "counter"})])
    result = call_subagent_json(client, SubagentRole.analist, {})
    assert result["archetype"] == "A1"
    assert client.call_count == 1


def test_call_subagent_json_retries_once_on_invalid_json():
    client = ScriptedClient(
        ["not json", json.dumps({"archetype": "A1", "recommended_state": "counter"})]
    )
    result = call_subagent_json(client, SubagentRole.analist, {})
    assert result["archetype"] == "A1"
    assert client.call_count == 2


def test_call_subagent_json_escalates_after_retries_exhausted():
    client = ScriptedClient(["not json", "still not json"])
    with pytest.raises(SubagentEscalated) as exc_info:
        call_subagent_json(client, SubagentRole.analist, {})
    assert exc_info.value.role is SubagentRole.analist
    assert client.call_count == 2


def test_call_subagent_json_escalates_on_missing_required_key():
    # Kritik requires "verdict"; this response is valid JSON but incomplete.
    client = ScriptedClient([json.dumps({"violations": []}), json.dumps({"violations": []})])
    with pytest.raises(SubagentEscalated):
        call_subagent_json(client, SubagentRole.kritik, {})
