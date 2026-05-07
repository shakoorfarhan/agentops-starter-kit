import pytest

from agentops_starter import (
    GuardrailError,
    explore_workspace,
    run_bugfix_workflow,
    run_feature_workflow,
    run_refactor_workflow,
)


def test_explore_workspace_reports_key_files_and_tests(tmp_path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_smoke.py").write_text("def test_ok(): pass\n", encoding="utf-8")

    report = explore_workspace(tmp_path)

    assert "README.md" in report.key_files
    assert "pyproject.toml" in report.key_files
    assert "tests/test_smoke.py" in report.test_files
    assert "Explore Report" in report.to_markdown()


def test_bugfix_workflow_reports_failing_test(tmp_path) -> None:
    report = run_bugfix_workflow(
        tmp_path,
        task="fix parser failure",
        test_command=["uv", "run", "pytest", "missing_test.py"],
    )

    assert report.status == "needs_fix"
    assert report.test_result.returncode != 0
    assert "Bugfix Report" in report.to_markdown()
    assert any("focused regression test" in step for step in report.plan)


def test_bugfix_workflow_refuses_passing_test_by_default(tmp_path) -> None:
    report = run_bugfix_workflow(
        tmp_path,
        task="fix parser failure",
        test_command=["pwd"],
    )

    assert report.status == "refused_passing_test"
    assert "already passes" in report.plan[0]


def test_bugfix_workflow_can_plan_from_passing_test_when_allowed(tmp_path) -> None:
    report = run_bugfix_workflow(
        tmp_path,
        task="fix parser failure",
        test_command=["pwd"],
        allow_passing=True,
    )

    assert report.status == "planning_from_passing_test"
    assert report.test_result.returncode == 0


def test_bugfix_workflow_blocks_destructive_test_command(tmp_path) -> None:
    with pytest.raises(GuardrailError):
        run_bugfix_workflow(
            tmp_path,
            task="fix parser failure",
            test_command=["git", "reset", "--hard"],
        )


def test_feature_workflow_requires_acceptance_criteria(tmp_path) -> None:
    with pytest.raises(ValueError):
        run_feature_workflow(
            tmp_path,
            task="add markdown export",
            acceptance_criteria=[],
        )


def test_feature_workflow_creates_plan_without_baseline_command(tmp_path) -> None:
    report = run_feature_workflow(
        tmp_path,
        task="add markdown export",
        acceptance_criteria=["exports markdown file", "keeps existing tests passing"],
    )

    assert report.status == "ready_to_plan"
    assert report.test_result is None
    assert "Feature Report" in report.to_markdown()
    assert any("acceptance criteria" in step.lower() for step in report.plan)


def test_feature_workflow_records_passing_baseline(tmp_path) -> None:
    report = run_feature_workflow(
        tmp_path,
        task="add markdown export",
        acceptance_criteria=["exports markdown file"],
        test_command=["pwd"],
    )

    assert report.status == "ready_to_plan"
    assert report.test_result is not None
    assert report.test_result.returncode == 0


def test_feature_workflow_marks_failing_baseline(tmp_path) -> None:
    report = run_feature_workflow(
        tmp_path,
        task="add markdown export",
        acceptance_criteria=["exports markdown file"],
        test_command=["uv", "run", "pytest", "missing_test.py"],
    )

    assert report.status == "baseline_failing"
    assert report.test_result is not None
    assert report.test_result.returncode != 0


def test_feature_workflow_blocks_destructive_baseline_command(tmp_path) -> None:
    with pytest.raises(GuardrailError):
        run_feature_workflow(
            tmp_path,
            task="add markdown export",
            acceptance_criteria=["exports markdown file"],
            test_command=["git", "reset", "--hard"],
        )


def test_refactor_workflow_requires_passing_preservation_check(tmp_path) -> None:
    report = run_refactor_workflow(
        tmp_path,
        task="split parser module",
        preserve_command=["pwd"],
    )

    assert report.status == "ready_to_plan"
    assert report.preserve_result.returncode == 0
    assert "Refactor Report" in report.to_markdown()
    assert any("external behavior unchanged" in step for step in report.plan)


def test_refactor_workflow_blocks_when_preservation_check_fails(tmp_path) -> None:
    report = run_refactor_workflow(
        tmp_path,
        task="split parser module",
        preserve_command=["uv", "run", "pytest", "missing_test.py"],
    )

    assert report.status == "blocked_failing_preservation_check"
    assert report.preserve_result.returncode != 0
    assert "No files were changed." in report.plan


def test_refactor_workflow_blocks_destructive_preservation_command(tmp_path) -> None:
    with pytest.raises(GuardrailError):
        run_refactor_workflow(
            tmp_path,
            task="split parser module",
            preserve_command=["git", "reset", "--hard"],
        )
