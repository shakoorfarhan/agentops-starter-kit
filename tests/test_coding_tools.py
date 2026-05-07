import pytest

from agentops_starter import GuardrailError, Workspace


def test_workspace_blocks_path_escape(tmp_path) -> None:
    workspace = Workspace(tmp_path)

    with pytest.raises(GuardrailError):
        workspace.resolve("../outside.txt")


def test_workspace_search_text_finds_matches(tmp_path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text(
        "def run_agent():\n    return 'ok'\n", encoding="utf-8"
    )
    workspace = Workspace(tmp_path)

    matches = workspace.search_text("run_agent")

    assert matches == ["src/app.py:1: def run_agent():"]


def test_workspace_blocks_destructive_commands(tmp_path) -> None:
    workspace = Workspace(tmp_path)

    with pytest.raises(GuardrailError):
        workspace.run_command(["git", "reset", "--hard"])


def test_workspace_allows_safe_commands(tmp_path) -> None:
    workspace = Workspace(tmp_path)

    result = workspace.run_command(["pwd"])

    assert result.returncode == 0
    assert str(tmp_path) in result.stdout
