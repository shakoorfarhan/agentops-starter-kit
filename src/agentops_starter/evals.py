"""Lightweight eval runner for deterministic agent behavior checks."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from agentops_starter.agent import Agent, AgentResult


@dataclass(frozen=True)
class EvalCase:
    """One behavior expectation for an agent."""

    name: str
    task: str
    assert_result: Callable[[AgentResult], bool]


@dataclass(frozen=True)
class EvalResult:
    """Aggregate eval result."""

    total: int
    passed: int
    failures: tuple[str, ...]

    @property
    def score(self) -> float:
        if self.total == 0:
            return 0.0
        return self.passed / self.total


def run_eval(agent: Agent, cases: list[EvalCase]) -> EvalResult:
    failures: list[str] = []

    for case in cases:
        result = agent.run(case.task)
        if not case.assert_result(result):
            failures.append(case.name)

    return EvalResult(total=len(cases), passed=len(cases) - len(failures), failures=tuple(failures))
