"""Telemetry primitives for observable agent runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter


@dataclass(frozen=True)
class TraceEvent:
    """Single model/tool/budget event in an agent run."""

    kind: str
    message: str
    elapsed_ms: float
    metadata: dict[str, str | int | float | bool] = field(default_factory=dict)


class TraceRecorder:
    """Records lightweight trace events and cost estimates."""

    def __init__(self) -> None:
        self._started_at = perf_counter()
        self.events: list[TraceEvent] = []
        self.total_cost_usd = 0.0
        self.input_tokens = 0
        self.output_tokens = 0

    def record(
        self,
        kind: str,
        message: str,
        *,
        metadata: dict[str, str | int | float | bool] | None = None,
    ) -> None:
        self.events.append(
            TraceEvent(
                kind=kind,
                message=message,
                elapsed_ms=(perf_counter() - self._started_at) * 1000,
                metadata=metadata or {},
            )
        )

    def record_model_usage(
        self,
        *,
        input_tokens: int,
        output_tokens: int,
        estimated_cost_usd: float,
    ) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_cost_usd += estimated_cost_usd
        self.record(
            "model_usage",
            "Model call completed",
            metadata={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost_usd": round(estimated_cost_usd, 6),
            },
        )

    def summary(self) -> str:
        return (
            f"{len(self.events)} events, "
            f"{self.input_tokens} input tokens, "
            f"{self.output_tokens} output tokens, "
            f"${self.total_cost_usd:.4f} estimated"
        )
