"""Command-line demo for the starter kit."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path

from agentops_starter.agent import Agent, AgentConfig
from agentops_starter.coding_agent import (
    explore_workspace,
    run_bugfix_workflow,
    run_feature_workflow,
    run_refactor_workflow,
)
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

    code = subparsers.add_parser("code", help="Run local coding-agent workflows")
    code_subparsers = code.add_subparsers(dest="code_command")

    explore = code_subparsers.add_parser("explore", help="Inspect a repo without editing files")
    explore.add_argument("path", nargs="?", default=".")

    bugfix = code_subparsers.add_parser("bugfix", help="Plan a guarded bugfix from a test command")
    bugfix.add_argument("path", nargs="?", default=".")
    bugfix.add_argument("--task", required=True, help="Bugfix task description")
    bugfix.add_argument(
        "--test",
        required=True,
        help="Focused test command, e.g. 'uv run pytest tests/test_parser.py'",
    )
    bugfix.add_argument(
        "--allow-passing",
        action="store_true",
        help="Continue planning even if the provided test command passes",
    )

    feature = code_subparsers.add_parser(
        "feature",
        help="Plan an acceptance-driven feature change",
    )
    feature.add_argument("path", nargs="?", default=".")
    feature.add_argument("--task", required=True, help="Feature task description")
    feature.add_argument(
        "--accept",
        action="append",
        required=True,
        help="Acceptance criterion. Repeat for multiple criteria.",
    )
    feature.add_argument(
        "--test",
        default=None,
        help="Optional baseline test command, e.g. 'uv run pytest'",
    )

    refactor = code_subparsers.add_parser(
        "refactor",
        help="Plan a behavior-preserving refactor",
    )
    refactor.add_argument("path", nargs="?", default=".")
    refactor.add_argument("--task", required=True, help="Refactor task description")
    refactor.add_argument(
        "--preserve",
        required=True,
        help="Behavior preservation command, e.g. 'uv run pytest'",
    )

    args = parser.parse_args()

    if args.command == "init":
        result = init_project(Path(args.path), force=args.force)
        print(f"Created {len(result.files_created)} files in {result.path}")
        return 0

    if args.command == "code" and args.code_command == "explore":
        report = explore_workspace(Path(args.path))
        print(report.to_markdown())
        return 0

    if args.command == "code" and args.code_command == "bugfix":
        report = run_bugfix_workflow(
            Path(args.path),
            task=args.task,
            test_command=shlex.split(args.test),
            allow_passing=args.allow_passing,
        )
        print(report.to_markdown())
        return 0 if report.status != "refused_passing_test" else 2

    if args.command == "code" and args.code_command == "feature":
        test_command = shlex.split(args.test) if args.test else None
        report = run_feature_workflow(
            Path(args.path),
            task=args.task,
            acceptance_criteria=args.accept,
            test_command=test_command,
        )
        print(report.to_markdown())
        return 0 if report.status != "baseline_failing" else 3

    if args.command == "code" and args.code_command == "refactor":
        report = run_refactor_workflow(
            Path(args.path),
            task=args.task,
            preserve_command=shlex.split(args.preserve),
        )
        print(report.to_markdown())
        return 0 if report.status == "ready_to_plan" else 4

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
