from agentops_starter.tools import ToolCall, ToolRegistry, default_tool_registry


def test_unknown_tool_returns_error_result() -> None:
    registry = ToolRegistry()

    result = registry.execute(ToolCall(name="missing", input={}))

    assert result.ok is False
    assert result.error == "Unknown tool: missing"


def test_summarize_text_tool_returns_short_summary() -> None:
    registry = default_tool_registry()

    result = registry.execute(
        ToolCall(
            name="summarize_text",
            input={"text": "one two three four five six seven eight nine ten"},
        )
    )

    assert result.ok is True
    assert result.output.startswith("one two three")


def test_save_note_writes_markdown_file(tmp_path) -> None:
    registry = default_tool_registry()

    result = registry.execute(
        ToolCall(
            name="save_note",
            input={"title": "demo", "body": "hello", "output_dir": str(tmp_path)},
        )
    )

    assert result.ok is True
    assert (tmp_path / "demo.md").read_text(encoding="utf-8") == "# demo\n\nhello\n"
