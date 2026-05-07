"""Model provider abstractions for deterministic and real LLM backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


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
