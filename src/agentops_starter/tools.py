"""Tool registry and example tools."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter


class ToolError(Exception):
    """Raised when a tool cannot complete safely."""


@dataclass(frozen=True)
class ToolCall:
    """A request to execute a named tool."""

    name: str
    input: dict[str, str]


@dataclass(frozen=True)
class ToolResult:
    """Structured result from tool execution."""

    name: str
    ok: bool
    output: str
    latency_ms: float
    error: str | None = None


@dataclass(frozen=True)
class Tool:
    """Registered tool metadata and implementation."""

    name: str
    description: str
    handler: Callable[[dict[str, str]], str]
    required_fields: tuple[str, ...] = field(default_factory=tuple)

    def execute(self, payload: dict[str, str]) -> ToolResult:
        start = perf_counter()
        try:
            missing = [field for field in self.required_fields if not payload.get(field)]
            if missing:
                raise ToolError(f"Missing required field(s): {', '.join(missing)}")
            output = self.handler(payload)
            return ToolResult(
                name=self.name,
                ok=True,
                output=output,
                latency_ms=(perf_counter() - start) * 1000,
            )
        except Exception as exc:  # noqa: BLE001 - tool failures are returned to the agent.
            return ToolResult(
                name=self.name,
                ok=False,
                output="",
                latency_ms=(perf_counter() - start) * 1000,
                error=str(exc),
            )


class ToolRegistry:
    """In-memory registry for safe tool discovery and execution."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def names(self) -> list[str]:
        return sorted(self._tools)

    def execute(self, call: ToolCall) -> ToolResult:
        tool = self._tools.get(call.name)
        if tool is None:
            return ToolResult(
                name=call.name,
                ok=False,
                output="",
                latency_ms=0.0,
                error=f"Unknown tool: {call.name}",
            )
        return tool.execute(call.input)


def _summarize_text(payload: dict[str, str]) -> str:
    text = payload["text"].strip()
    words = text.split()
    summary = " ".join(words[:24])
    if len(words) > 24:
        summary += "..."
    return summary


def _save_note(payload: dict[str, str]) -> str:
    title = payload["title"].strip().replace("/", "-")
    body = payload["body"].strip()
    output_dir = Path(payload.get("output_dir", "runs"))
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{title}.md"
    path.write_text(f"# {title}\n\n{body}\n", encoding="utf-8")
    return str(path)


def default_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        Tool(
            name="summarize_text",
            description="Summarize text into a short note.",
            handler=_summarize_text,
            required_fields=("text",),
        )
    )
    registry.register(
        Tool(
            name="save_note",
            description="Save a markdown note to disk.",
            handler=_save_note,
            required_fields=("title", "body"),
        )
    )
    return registry
