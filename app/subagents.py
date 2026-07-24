"""Subagent prompt loading + JSON contract enforcement (draft).

Subagent system prompts live as plain Markdown under app/prompts/*.md (see
app/prompts/README.md for the turn flow) so a prompt update is a git push,
not a code change. Every subagent is contracted to return JSON only; a bad
response gets one retry, then the caller should escalate to a human.
"""

import enum
import json
from pathlib import Path
from typing import Protocol

DEFAULT_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


class SubagentRole(str, enum.Enum):
    stratejist = "stratejist"
    yazici = "yazici"
    kritik = "kritik"
    analist = "analist"
    intake = "intake"


# app/prompts/README.md: "Yazıcı/Stratejist için sonnet, Analist/Kritik için
# haiku yeterli olabilir — maliyet ölçümüyle karar ver." Advisory only.
# Intake is a natural-conversation role, grouped with Yazıcı/Stratejist.
SUBAGENT_MODEL_HINTS: dict[SubagentRole, str] = {
    SubagentRole.stratejist: "sonnet",
    SubagentRole.yazici: "sonnet",
    SubagentRole.kritik: "haiku",
    SubagentRole.analist: "haiku",
    SubagentRole.intake: "sonnet",
}

_REQUIRED_KEYS: dict[SubagentRole, tuple[str, ...]] = {
    SubagentRole.stratejist: ("anchor", "target", "floor", "concession_ladder", "primary_tactics"),
    SubagentRole.yazici: ("message", "tactic_used"),
    SubagentRole.kritik: ("verdict",),
    SubagentRole.analist: ("archetype", "recommended_state"),
    SubagentRole.intake: ("reply", "collected_fields", "missing_fields", "ready"),
}


class Verdict(str, enum.Enum):
    approve = "APPROVE"
    revise = "REVISE"
    reject = "REJECT"
    escalate = "ESCALATE"


class SubagentParseError(Exception):
    """A subagent's response wasn't valid JSON or was missing required keys."""


class SubagentEscalated(Exception):
    """Raised once a subagent has failed to produce a usable response after retrying."""

    def __init__(self, role: SubagentRole, reason: str):
        self.role = role
        self.reason = reason
        super().__init__(f"{role.value} escalated: {reason}")


def load_subagent_prompt(role: SubagentRole, prompts_dir: Path | str = DEFAULT_PROMPTS_DIR) -> str:
    """Read a subagent's system prompt from app/prompts/<role>.md, fresh every call."""
    return (Path(prompts_dir) / f"{role.value}.md").read_text(encoding="utf-8")


class SubagentClient(Protocol):
    """The seam a real LLM integration implements (e.g. the Anthropic Messages API)."""

    def complete(self, role: SubagentRole, system_prompt: str, payload: dict) -> str:
        """Return the raw text response for a subagent call (expected: pure JSON)."""
        ...


def _parse_and_validate(role: SubagentRole, raw: str) -> dict:
    data = json.loads(raw)
    missing = [key for key in _REQUIRED_KEYS[role] if key not in data]
    if missing:
        raise SubagentParseError(f"missing keys: {missing}")
    return data


def call_subagent_json(
    client: SubagentClient,
    role: SubagentRole,
    payload: dict,
    prompts_dir: Path | str = DEFAULT_PROMPTS_DIR,
    max_retries: int = 1,
) -> dict:
    """Call a subagent and parse its JSON response, retrying once on a bad response.

    Raises SubagentEscalated once the response is still unusable after
    retrying — callers route that to the human-in-the-loop queue (ESCALATE).
    """
    system_prompt = load_subagent_prompt(role, prompts_dir)

    last_error = ""
    for _ in range(max_retries + 1):
        raw = client.complete(role, system_prompt, payload)
        try:
            return _parse_and_validate(role, raw)
        except (json.JSONDecodeError, SubagentParseError) as exc:
            last_error = str(exc)

    raise SubagentEscalated(role, last_error)
