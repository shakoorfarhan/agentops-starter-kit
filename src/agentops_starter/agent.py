"""Observable agent loop with bounded retries and budget checks."""

from __future__ import annotations

from dataclasses import dataclass, field

from agentops_starter.models import ModelProvider, ModelRequest
from agentops_starter.telemetry import TraceRecorder
from agentops_starter.tools import ToolCall, ToolRegistry


@dataclass(frozen=True)
class RetryPolicy:
    """Retry settings for failed tool calls."""

    max_tool_retries: int = 1


@dataclass(frozen=True)
class AgentConfig:
    """Runtime limits for an agent run."""

    max_steps: int = 6
    budget_usd: float = 0.10
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)


@dataclass(frozen=True)
class AgentResult:
    """Final result returned by the agent."""

    final_answer: str
    trace: TraceRecorder
    success: bool


class Agent:
    """Small but production-shaped agent loop."""

    def __init__(
        self,
        *,
        model: ModelProvider,
        tools: ToolRegistry,
        config: AgentConfig | None = None,
    ) -> None:
        self._model = model
        self._tools = tools
        self._config = config or AgentConfig()

    def run(self, task: str) -> AgentResult:
        trace = TraceRecorder()
        scratchpad: list[str] = []
        tool_failures: dict[str, int] = {}
        trace.record("run_started", "Agent run started", metadata={"task": task})

        for step in range(1, self._config.max_steps + 1):
            if trace.total_cost_usd > self._config.budget_usd:
                trace.record("budget_exceeded", "Budget exceeded", metadata={"step": step})
                return AgentResult(
                    final_answer="Stopped because the run exceeded its budget.",
                    trace=trace,
                    success=False,
                )

            response = self._model.complete(
                ModelRequest(
                    task=task,
                    scratchpad=scratchpad,
                    available_tools=self._tools.names(),
                )
            )
            trace.record("model_thought", response.thought, metadata={"step": step})
            trace.record_model_usage(
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                estimated_cost_usd=response.estimated_cost_usd,
            )

            if response.final_answer is not None:
                trace.record(
                    "run_completed",
                    "Agent produced final answer",
                    metadata={"step": step},
                )
                return AgentResult(final_answer=response.final_answer, trace=trace, success=True)

            if not response.wants_tool:
                trace.record(
                    "run_completed",
                    "Agent stopped without tool call",
                    metadata={"step": step},
                )
                return AgentResult(final_answer=response.thought, trace=trace, success=True)

            call = ToolCall(name=response.tool_name or "", input=response.tool_input)
            result = self._tools.execute(call)
            trace.record(
                "tool_call",
                f"Tool {call.name} completed" if result.ok else f"Tool {call.name} failed",
                metadata={
                    "tool": call.name,
                    "ok": result.ok,
                    "latency_ms": round(result.latency_ms, 2),
                },
            )

            if result.ok:
                scratchpad.append(f"tool_result:{call.name}:{result.output}")
                continue

            failures = tool_failures.get(call.name, 0) + 1
            tool_failures[call.name] = failures
            scratchpad.append(f"tool_error:{call.name}:{result.error}")
            if failures > self._config.retry_policy.max_tool_retries:
                trace.record(
                    "run_failed",
                    "Tool retry limit exceeded",
                    metadata={"tool": call.name},
                )
                return AgentResult(
                    final_answer=f"Stopped after tool failure: {result.error}",
                    trace=trace,
                    success=False,
                )

        trace.record("run_failed", "Maximum step count reached")
        return AgentResult(
            final_answer="Stopped because the run reached the maximum step count.",
            trace=trace,
            success=False,
        )
