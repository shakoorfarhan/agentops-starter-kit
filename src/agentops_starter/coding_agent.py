"""Local coding-agent workflows with explicit guardrails."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from agentops_starter.coding_tools import CommandResult, Workspace


@dataclass(frozen=True)
class ExploreReport:
    """Read-only summary of a local code workspace."""

    root: Path
    total_files_sampled: int
    top_extensions: tuple[tuple[str, int], ...]
    key_files: tuple[str, ...]
    test_files: tuple[str, ...]

    def to_markdown(self) -> str:
        extension_lines = "\n".join(
            f"- `{extension or '[no extension]'}`: {count}"
            for extension, count in self.top_extensions
        )
        key_file_lines = "\n".join(f"- `{path}`" for path in self.key_files) or "- None found"
        test_file_lines = (
            "\n".join(f"- `{path}`" for path in self.test_files[:20]) or "- None found"
        )
        return (
            f"# Explore Report\n\n"
            f"Root: `{self.root}`\n\n"
            f"Files sampled: {self.total_files_sampled}\n\n"
            f"## Top Extensions\n\n{extension_lines}\n\n"
            f"## Key Files\n\n{key_file_lines}\n\n"
            f"## Test Files\n\n{test_file_lines}\n"
        )


@dataclass(frozen=True)
class BugfixReport:
    """Verification-first bugfix workflow output."""

    root: Path
    task: str
    test_command: tuple[str, ...]
    test_result: CommandResult
    status: str
    plan: tuple[str, ...]

    def to_markdown(self) -> str:
        plan_lines = "\n".join(f"{index}. {step}" for index, step in enumerate(self.plan, start=1))
        stderr = self.test_result.stderr.strip() or "[empty]"
        stdout = self.test_result.stdout.strip() or "[empty]"
        return (
            "# Bugfix Report\n\n"
            f"Root: `{self.root}`\n\n"
            f"Task: {self.task}\n\n"
            f"Status: `{self.status}`\n\n"
            f"Test command: `{' '.join(self.test_command)}`\n\n"
            f"Exit code: `{self.test_result.returncode}`\n\n"
            f"## Plan\n\n{plan_lines}\n\n"
            f"## Test Stdout\n\n```text\n{stdout}\n```\n\n"
            f"## Test Stderr\n\n```text\n{stderr}\n```\n"
        )


@dataclass(frozen=True)
class FeatureReport:
    """Acceptance-driven feature workflow output."""

    root: Path
    task: str
    acceptance_criteria: tuple[str, ...]
    test_command: tuple[str, ...] | None
    test_result: CommandResult | None
    status: str
    plan: tuple[str, ...]

    def to_markdown(self) -> str:
        criteria_lines = "\n".join(f"- {criterion}" for criterion in self.acceptance_criteria)
        plan_lines = "\n".join(f"{index}. {step}" for index, step in enumerate(self.plan, start=1))
        test_section = "No test command provided."
        if self.test_result is not None and self.test_command is not None:
            stdout = self.test_result.stdout.strip() or "[empty]"
            stderr = self.test_result.stderr.strip() or "[empty]"
            test_section = (
                f"Test command: `{' '.join(self.test_command)}`\n\n"
                f"Exit code: `{self.test_result.returncode}`\n\n"
                f"### Stdout\n\n```text\n{stdout}\n```\n\n"
                f"### Stderr\n\n```text\n{stderr}\n```"
            )
        return (
            "# Feature Report\n\n"
            f"Root: `{self.root}`\n\n"
            f"Task: {self.task}\n\n"
            f"Status: `{self.status}`\n\n"
            f"## Acceptance Criteria\n\n{criteria_lines}\n\n"
            f"## Plan\n\n{plan_lines}\n\n"
            f"## Baseline Check\n\n{test_section}\n"
        )


@dataclass(frozen=True)
class RefactorReport:
    """Behavior-preserving refactor workflow output."""

    root: Path
    task: str
    preserve_command: tuple[str, ...]
    preserve_result: CommandResult
    status: str
    plan: tuple[str, ...]

    def to_markdown(self) -> str:
        plan_lines = "\n".join(f"{index}. {step}" for index, step in enumerate(self.plan, start=1))
        stdout = self.preserve_result.stdout.strip() or "[empty]"
        stderr = self.preserve_result.stderr.strip() or "[empty]"
        return (
            "# Refactor Report\n\n"
            f"Root: `{self.root}`\n\n"
            f"Task: {self.task}\n\n"
            f"Status: `{self.status}`\n\n"
            f"Preservation command: `{' '.join(self.preserve_command)}`\n\n"
            f"Exit code: `{self.preserve_result.returncode}`\n\n"
            f"## Plan\n\n{plan_lines}\n\n"
            f"## Preservation Stdout\n\n```text\n{stdout}\n```\n\n"
            f"## Preservation Stderr\n\n```text\n{stderr}\n```\n"
        )


def explore_workspace(root: Path) -> ExploreReport:
    """Inspect a workspace without modifying files."""

    workspace = Workspace(root)
    files = workspace.list_files(max_files=500)
    extension_counts = Counter(path.suffix for path in files)
    key_names = {
        "README.md",
        "AGENTS.md",
        "pyproject.toml",
        "package.json",
        "uv.lock",
        "requirements.txt",
        "Makefile",
    }
    key_files = tuple(str(path) for path in files if path.name in key_names)
    test_files = tuple(
        str(path)
        for path in files
        if path.name.startswith("test_") or "/tests/" in f"/{path.as_posix()}"
    )

    return ExploreReport(
        root=workspace.root,
        total_files_sampled=len(files),
        top_extensions=tuple(extension_counts.most_common(8)),
        key_files=key_files,
        test_files=test_files,
    )


def run_bugfix_workflow(
    root: Path,
    *,
    task: str,
    test_command: list[str],
    allow_passing: bool = False,
) -> BugfixReport:
    """Run a guarded bugfix workflow without editing files."""

    workspace = Workspace(root)
    result = workspace.run_command(test_command)
    if result.returncode == 0 and not allow_passing:
        return BugfixReport(
            root=workspace.root,
            task=task,
            test_command=tuple(test_command),
            test_result=result,
            status="refused_passing_test",
            plan=(
                "The provided test command already passes.",
                "Provide a failing regression test or use --allow-passing to continue planning.",
                "No files were changed.",
            ),
        )

    return BugfixReport(
        root=workspace.root,
        task=task,
        test_command=tuple(test_command),
        test_result=result,
        status="needs_fix" if result.returncode != 0 else "planning_from_passing_test",
        plan=_bugfix_plan(task=task, test_result=result),
    )


def run_feature_workflow(
    root: Path,
    *,
    task: str,
    acceptance_criteria: list[str],
    test_command: list[str] | None = None,
) -> FeatureReport:
    """Create a guarded feature implementation plan."""

    if not acceptance_criteria:
        raise ValueError("At least one acceptance criterion is required")

    workspace = Workspace(root)
    test_result = workspace.run_command(test_command) if test_command else None
    status = "ready_to_plan"
    if test_result is not None and test_result.returncode != 0:
        status = "baseline_failing"

    return FeatureReport(
        root=workspace.root,
        task=task,
        acceptance_criteria=tuple(acceptance_criteria),
        test_command=tuple(test_command) if test_command else None,
        test_result=test_result,
        status=status,
        plan=_feature_plan(task=task, acceptance_criteria=acceptance_criteria),
    )


def run_refactor_workflow(
    root: Path,
    *,
    task: str,
    preserve_command: list[str],
) -> RefactorReport:
    """Create a guarded refactor plan after behavior preservation is checked."""

    workspace = Workspace(root)
    result = workspace.run_command(preserve_command)
    if result.returncode != 0:
        return RefactorReport(
            root=workspace.root,
            task=task,
            preserve_command=tuple(preserve_command),
            preserve_result=result,
            status="blocked_failing_preservation_check",
            plan=(
                "The preservation command is failing before refactor work starts.",
                "Fix or narrow the baseline check before changing structure.",
                "No files were changed.",
            ),
        )

    return RefactorReport(
        root=workspace.root,
        task=task,
        preserve_command=tuple(preserve_command),
        preserve_result=result,
        status="ready_to_plan",
        plan=_refactor_plan(task=task),
    )


def _bugfix_plan(*, task: str, test_result: CommandResult) -> tuple[str, ...]:
    failure_source = "stderr" if test_result.stderr.strip() else "stdout"
    return (
        f"Confirm the bug scope from the task: {task}",
        f"Inspect the failing {failure_source} and identify the first actionable error.",
        "Search for the failing symbol, file path, or assertion message in the workspace.",
        "Add or keep a focused regression test that fails before the fix.",
        "Make the smallest code change that addresses the failure.",
        "Run the focused test command again.",
        "Run lint and any adjacent tests before committing.",
    )


def _feature_plan(*, task: str, acceptance_criteria: list[str]) -> tuple[str, ...]:
    criteria_summary = "; ".join(acceptance_criteria)
    return (
        f"Confirm the feature scope from the task: {task}",
        f"Translate acceptance criteria into focused tests or evals: {criteria_summary}",
        "Inspect existing modules and choose the smallest compatible extension point.",
        "Add failing tests/evals for the expected behavior before implementation.",
        "Implement the feature in small, reviewable changes.",
        "Run the focused tests/evals and update docs or examples.",
        "Run lint and the relevant broader test suite before committing.",
    )


def _refactor_plan(*, task: str) -> tuple[str, ...]:
    return (
        f"Confirm the refactor goal and non-goals: {task}",
        "Keep external behavior unchanged unless explicitly requested.",
        "Identify the smallest module boundary that can absorb the refactor.",
        "Move or rename code in small steps while preserving public interfaces.",
        "Run the preservation command after each meaningful step.",
        "Update internal docs or comments only where structure becomes clearer.",
        "Run lint and adjacent tests before committing.",
    )
