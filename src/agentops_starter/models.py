"""Model provider abstractions for deterministic and real LLM backends."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Protocol
from urllib import error as urlerror
from urllib import request as urlrequest


@dataclass(frozen=True)
class ModelRequest:
    """Input sent to a model provider."""

    task: str
    scratchpad: list[str] = field(default_factory=list)
    available_tools: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ModelResponse:
    """Structured model decision consumed by the agent loop."""

    thought: str
    final_answer: str | None = None
    tool_name: str | None = None
    tool_input: dict[str, str] = field(default_factory=dict)
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0

    @property
    def wants_tool(self) -> bool:
        return self.tool_name is not None


class ModelProvider(Protocol):
    """Protocol real LLM providers and test doubles must implement."""

    def complete(self, request: ModelRequest) -> ModelResponse:
        """Return the next agent decision."""


class FakeModelProvider:
    """Deterministic provider used by examples and tests.

    It chooses one tool based on keywords and then returns a final answer after
    the first tool result appears in the scratchpad.
    """

    def complete(self, request: ModelRequest) -> ModelResponse:
        text = request.task.lower()
        has_tool_result = any(item.startswith("tool_result:") for item in request.scratchpad)
        token_estimate = max(1, len(request.task.split()))

        if has_tool_result:
            return ModelResponse(
                thought="I have enough tool context to answer.",
                final_answer="Completed the task using available tools.",
                input_tokens=token_estimate + 20,
                output_tokens=8,
                estimated_cost_usd=0.0002,
            )

        if "save" in text or "write" in text:
            return ModelResponse(
                thought="The user wants an artifact saved.",
                tool_name="save_note",
                tool_input={"title": "agent-output", "body": request.task},
                input_tokens=token_estimate,
                output_tokens=12,
                estimated_cost_usd=0.0002,
            )

        if "summarize" in text or "research" in text:
            return ModelResponse(
                thought="The task needs a concise research summary.",
                tool_name="summarize_text",
                tool_input={"text": request.task},
                input_tokens=token_estimate,
                output_tokens=12,
                estimated_cost_usd=0.0002,
            )

        return ModelResponse(
            thought="No tool is needed.",
            final_answer=f"Direct answer: {request.task}",
            input_tokens=token_estimate,
            output_tokens=10,
            estimated_cost_usd=0.0001,
        )


class OllamaModelProvider:
    """Local model provider for Ollama's `/api/generate` endpoint.

    This adapter intentionally uses the Python standard library so local/offline
    usage does not require extra dependencies.
    """

    def __init__(
        self,
        *,
        model: str = "llama3.2",
        base_url: str = "http://127.0.0.1:11434",
        timeout_seconds: float = 60.0,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def complete(self, request: ModelRequest) -> ModelResponse:
        prompt = self._build_prompt(request)
        payload = json.dumps(
            {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0},
            }
        ).encode("utf-8")
        http_request = urlrequest.Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlrequest.urlopen(http_request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except urlerror.URLError as exc:
            return ModelResponse(
                thought=f"Ollama request failed: {exc}",
                final_answer="Local model unavailable. Start Ollama or use the fake provider.",
            )

        data = json.loads(raw)
        generated = data.get("response", "{}")
        return self._parse_response(generated, request.task)

    def _build_prompt(self, request: ModelRequest) -> str:
        return (
            "You are an agent controller. Respond only as JSON with keys: "
            "thought, final_answer, tool_name, tool_input.\n"
            f"Task: {request.task}\n"
            f"Available tools: {', '.join(request.available_tools)}\n"
            f"Scratchpad: {request.scratchpad}\n"
            "If a tool is useful, set final_answer to null and choose one tool. "
            "If the task is complete, set tool_name to null and provide final_answer."
        )

    def _parse_response(self, generated: str, task: str) -> ModelResponse:
        try:
            parsed = json.loads(generated)
        except json.JSONDecodeError:
            return ModelResponse(
                thought="The local model returned non-JSON output.",
                final_answer=generated.strip() or f"Direct answer: {task}",
            )

        tool_name = parsed.get("tool_name")
        tool_input = parsed.get("tool_input")
        if not isinstance(tool_input, dict):
            tool_input = {}
        return ModelResponse(
            thought=str(parsed.get("thought") or "Local model response."),
            final_answer=parsed.get("final_answer"),
            tool_name=str(tool_name) if tool_name else None,
            tool_input={str(key): str(value) for key, value in tool_input.items()},
        )
