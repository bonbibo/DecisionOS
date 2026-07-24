from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.config import Settings
from app.llm import AnthropicSubagentClient, _model_for_role, _strip_json_fence
from app.models import LLMCall
from app.subagents import SubagentRole


class FakeAnthropicMessages:
    def __init__(self, text: str, input_tokens: int = 42, output_tokens: int = 7):
        self.text = text
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.last_kwargs: dict | None = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=self.text)],
            usage=SimpleNamespace(input_tokens=self.input_tokens, output_tokens=self.output_tokens),
        )


class FakeAnthropic:
    def __init__(self, text: str, **kwargs):
        self.messages = FakeAnthropicMessages(text, **kwargs)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ('```json\n{"a": 1}\n```', '{"a": 1}'),
        ('```\n{"a": 1}\n```', '{"a": 1}'),
        ('{"a": 1}', '{"a": 1}'),
        ('  {"a": 1}  ', '{"a": 1}'),
    ],
)
def test_strip_json_fence(raw, expected):
    assert _strip_json_fence(raw) == expected


def test_model_for_role_reads_from_settings():
    settings = Settings(
        model_yazici="yazici-model",
        model_stratejist="stratejist-model",
        model_analist="analist-model",
        model_kritik="kritik-model",
    )
    assert _model_for_role(SubagentRole.yazici, settings) == "yazici-model"
    assert _model_for_role(SubagentRole.stratejist, settings) == "stratejist-model"
    assert _model_for_role(SubagentRole.analist, settings) == "analist-model"
    assert _model_for_role(SubagentRole.kritik, settings) == "kritik-model"


def test_complete_forces_json_and_strips_fence(db_session, make_case):
    case = make_case()
    fake_anthropic = FakeAnthropic('```json\n{"archetype": "A1"}\n```')
    client = AnthropicSubagentClient(case_id=case.id, db=db_session, client=fake_anthropic)

    result = client.complete(SubagentRole.analist, "You are Analist.", {"INCOMING": "merhaba"})

    assert result == '{"archetype": "A1"}'
    assert fake_anthropic.messages.last_kwargs["system"].endswith("SADECE geçerli JSON döndür.")
    assert fake_anthropic.messages.last_kwargs["model"] == client.settings.model_analist


def test_complete_logs_llm_call_row(db_session, make_case):
    case = make_case()
    fake_anthropic = FakeAnthropic('{"verdict": "APPROVE"}', input_tokens=100, output_tokens=25)
    client = AnthropicSubagentClient(case_id=case.id, db=db_session, client=fake_anthropic)

    client.complete(SubagentRole.kritik, "You are Kritik.", {"DRAFT": {}})

    rows = db_session.execute(select(LLMCall).where(LLMCall.case_id == case.id)).scalars().all()
    assert len(rows) == 1
    row = rows[0]
    assert row.role == "kritik"
    assert row.model == client.settings.model_kritik
    assert row.input_tokens == 100
    assert row.output_tokens == 25
    assert row.latency_ms >= 0
