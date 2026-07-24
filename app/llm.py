"""Anthropic-backed SubagentClient (draft).

Implements app.subagents.SubagentClient against the real Anthropic Messages
API: per-role model selection from Settings (env-driven), a forced-JSON
system-prompt suffix + code-fence stripping so app.subagents.call_subagent_json's
existing retry/escalate logic sees clean text, and a cost/latency log row
per call in llm_calls (case_id, role, model, input/output tokens, latency_ms).
"""

import json
import re
import time
import uuid
from typing import Any

import anthropic
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models import LLMCall
from app.subagents import SubagentRole

MAX_TOKENS = 1024

_JSON_FENCE_RE = re.compile(r"\A```(?:json)?\s*\n?(.*?)\n?```\s*\Z", re.DOTALL)

_MODEL_FOR_ROLE = {
    SubagentRole.stratejist: "model_stratejist",
    SubagentRole.yazici: "model_yazici",
    SubagentRole.analist: "model_analist",
    SubagentRole.kritik: "model_kritik",
}


def _model_for_role(role: SubagentRole, settings: Settings) -> str:
    return getattr(settings, _MODEL_FOR_ROLE[role])


def _strip_json_fence(text: str) -> str:
    """Strip a ```json ... ``` (or bare ```...```) fence, if the model added one."""
    match = _JSON_FENCE_RE.match(text.strip())
    return match.group(1).strip() if match else text.strip()


class AnthropicSubagentClient:
    """SubagentClient implementation backed by the Anthropic Messages API.

    One instance is bound to a single Case (via case_id) so every call it
    makes can be logged against that case. `client` is an injectable seam
    for tests: any object exposing `.messages.create(...)` with the same
    shape as `anthropic.Anthropic().messages` works.
    """

    def __init__(
        self,
        case_id: uuid.UUID,
        db: Session,
        settings: Settings | None = None,
        client: Any | None = None,
    ):
        self.case_id = case_id
        self.db = db
        self.settings = settings or get_settings()
        self._client = client or anthropic.Anthropic(api_key=self.settings.anthropic_api_key)

    def complete(self, role: SubagentRole, system_prompt: str, payload: dict) -> str:
        model = _model_for_role(role, self.settings)
        system = system_prompt.rstrip() + "\n\nSADECE geçerli JSON döndür."

        start = time.monotonic()
        response = self._client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": _payload_to_text(payload)}],
        )
        latency_ms = int((time.monotonic() - start) * 1000)

        text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")

        self.db.add(
            LLMCall(
                case_id=self.case_id,
                role=role.value,
                model=model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                latency_ms=latency_ms,
            )
        )
        self.db.commit()

        return _strip_json_fence(text)


def _payload_to_text(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False)
