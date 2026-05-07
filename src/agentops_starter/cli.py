"""Command-line demo for the starter kit."""

from __future__ import annotations

import argparse
from pathlib import Path

from agentops_starter.agent import Agent, AgentConfig
from agentops_starter.models import FakeModelProvider, OllamaModelProvider
from agentops_starter.scaffold import init_project
from agentops_starter.tools import default_tool_registry


def main() -> int:
    parser = argparse.ArgumentParser(description="AgentOps Starter Kit.")
    subparsers = parser.add_subparsers(dest="command")

    demo = subparsers.add_parser("demo", help="Run the local demo agent")
    demo.add_argument("task", nargs="?", default="Research AI agent reliability and save notes")
    demo.add_argument("--provider", choices=("fake", "ollama"), default="fake")
    demo.add_argument("--model", default="llama3.2", help="Ollama model name")

    init = subparsers.add_parser("init", help="Create a guarded AI-agent app")
    init.add_argument("path")
    init.add_argument("--force", action="store_true", help="Write into a non-empty directory")

    args = parser.parse_args()

    if args.command == "init":
        result = init_project(Path(args.path), force=args.force)
        print(f"Created {len(result.files_created)} files in {result.path}")
        return 0

    task = getattr(args, "task", None) or "Research AI agent reliability and save notes"
    provider = getattr(args, "provider", "fake")
    model_provider = (
        OllamaModelProvider(model=getattr(args, "model", "llama3.2"))
        if provider == "ollama"
        else FakeModelProvider()
    )

    agent = Agent(
        model=model_provider,
        tools=default_tool_registry(),
        config=AgentConfig(max_steps=4, budget_usd=0.05),
    )
    result = agent.run(task)

    print(result.final_answer)
    print(result.trace.summary())
    for event in result.trace.events:
        print(f"- {event.kind}: {event.message}")

    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
