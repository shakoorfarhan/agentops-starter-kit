"""AgentOps Starter Kit public API."""

from agentops_starter.agent import Agent, AgentConfig, AgentResult, RetryPolicy
from agentops_starter.coding_agent import (
    BugfixReport,
    ExploreReport,
    FeatureReport,
    RefactorReport,
    explore_workspace,
    run_bugfix_workflow,
    run_feature_workflow,
    run_refactor_workflow,
)
from agentops_starter.coding_tools import GuardrailError, Workspace
from agentops_starter.evals import EvalCase, EvalResult, run_eval
from agentops_starter.models import (
    FakeModelProvider,
    ModelProvider,
    ModelRequest,
    ModelResponse,
    OllamaModelProvider,
)
from agentops_starter.telemetry import TraceEvent, TraceRecorder
from agentops_starter.tools import (
    Tool,
    ToolCall,
    ToolError,
    ToolRegistry,
    ToolResult,
    default_tool_registry,
)

__all__ = [
    "Agent",
    "AgentConfig",
    "AgentResult",
    "BugfixReport",
    "EvalCase",
    "EvalResult",
    "ExploreReport",
    "FeatureReport",
    "FakeModelProvider",
    "GuardrailError",
    "ModelProvider",
    "ModelRequest",
    "ModelResponse",
    "OllamaModelProvider",
    "RefactorReport",
    "RetryPolicy",
    "Tool",
    "ToolCall",
    "ToolError",
    "ToolRegistry",
    "ToolResult",
    "TraceEvent",
    "TraceRecorder",
    "Workspace",
    "default_tool_registry",
    "explore_workspace",
    "run_bugfix_workflow",
    "run_eval",
    "run_feature_workflow",
    "run_refactor_workflow",
]
