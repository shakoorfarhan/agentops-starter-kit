# AgentOps Starter Kit

A small, production-minded Python starter kit for building AI agents that are observable, testable, and easy to extend.

This project is intentionally compact. It demonstrates the engineering pieces most agent demos skip:

- Tool registry with typed inputs and controlled failures
- Agent loop with retry policy and budget limits
- Telemetry for model calls, tool calls, latency, and estimated cost
- Deterministic fake model for tests and local demos
- Optional Ollama provider for local/offline LLM experiments
- Simple eval runner for checking agent behavior before shipping

![Terminal demo](docs/assets/terminal-demo.svg)

## Quick Start

```bash
uv sync --extra dev
uv run agentops demo "Summarize revenue.csv and save the result"
uv run pytest
```

The demo uses a deterministic fake model, so it runs without API keys.

Create a guarded AI-agent app:

```bash
uv run agentops init ../my-agent-app
cd ../my-agent-app
uv sync --extra dev
uv run pytest
```

Use a local Ollama model when available:

```bash
ollama serve
ollama pull llama3.2
uv run agentops demo --provider ollama --model llama3.2 "Plan a support triage agent"
```

## Project Layout

```text
agentops-starter-kit/
├── src/agentops_starter/
│   ├── agent.py          # Agent loop, retry policy, budget enforcement
│   ├── models.py         # Model provider protocol and fake provider
│   ├── scaffold.py       # Guarded project generator
│   ├── telemetry.py      # Run trace, cost, timing, event records
│   ├── tools.py          # Tool registry and example tools
│   └── evals.py          # Lightweight behavior evaluation
├── examples/
│   └── basic_research_agent.py
├── tests/
└── docs/assets/
```

## Why This Exists

Most portfolio agent projects show a prompt and an API call. That is not enough for real work.

This starter kit shows how to wrap an agent with operational guardrails:

- **Reliability:** retries are explicit and bounded.
- **Observability:** every model and tool action becomes a trace event.
- **Cost control:** token/cost estimates are tracked against a budget.
- **Testability:** the fake model makes tests deterministic.
- **Extensibility:** real model providers can implement one protocol.

## Example

```python
from agentops_starter import Agent, AgentConfig, FakeModelProvider, default_tool_registry

agent = Agent(
    model=FakeModelProvider(),
    tools=default_tool_registry(),
    config=AgentConfig(max_steps=4, budget_usd=0.05),
)

result = agent.run("Research AI agent reliability and save notes")

print(result.final_answer)
print(result.trace.summary())
```

## Adding a Real Model Provider

Implement the `ModelProvider` protocol:

```python
from agentops_starter.models import ModelProvider, ModelRequest, ModelResponse

class OpenAIProvider:
    def complete(self, request: ModelRequest) -> ModelResponse:
        # Call your model API here and map the response into ModelResponse.
        ...
```

Keep provider code behind this interface so the agent loop, tools, telemetry, and tests remain stable.

## Testing

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Portfolio Notes

This project is designed to be useful in job conversations. Be ready to explain:

- how the agent loop decides when to stop
- how tool failures are represented
- why deterministic model doubles matter
- where you would add streaming, persistence, auth, or a web dashboard
