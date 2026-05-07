"""Command-line demo for the starter kit."""

from __future__ import annotations

import argparse

from agentops_starter.agent import Agent, AgentConfig
from agentops_starter.models import FakeModelProvider
from agentops_starter.tools import default_tool_registry


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the AgentOps starter demo.")
    parser.add_argument("task", nargs="?", default="Research AI agent reliability and save notes")
    args = parser.parse_args()

    agent = Agent(
        model=FakeModelProvider(),
        tools=default_tool_registry(),
        config=AgentConfig(max_steps=4, budget_usd=0.05),
    )
    result = agent.run(args.task)

    print(result.final_answer)
    print(result.trace.summary())
    for event in result.trace.events:
        print(f"- {event.kind}: {event.message}")

    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
