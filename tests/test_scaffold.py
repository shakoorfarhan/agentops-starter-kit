from agentops_starter.scaffold import init_project


def test_init_project_creates_guarded_app(tmp_path) -> None:
    result = init_project(tmp_path / "demo-agent")

    assert (result.path / "AGENTS.md").exists()
    assert (result.path / ".github/workflows/quality.yml").exists()
    assert (result.path / "tests/test_smoke.py").exists()
    assert len(result.files_created) == 10


def test_init_project_refuses_non_empty_directory(tmp_path) -> None:
    target = tmp_path / "demo-agent"
    target.mkdir()
    (target / "existing.txt").write_text("x", encoding="utf-8")

    try:
        init_project(target)
    except FileExistsError as exc:
        assert "not empty" in str(exc)
    else:
        raise AssertionError("Expected FileExistsError")
