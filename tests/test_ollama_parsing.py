from agentops_starter.models import OllamaModelProvider


def test_ollama_provider_tolerates_string_tool_input() -> None:
    provider = OllamaModelProvider()

    response = provider._parse_response(  # noqa: SLF001 - parser regression test
        '{"thought": "use a tool", "tool_name": "summarize_text", "tool_input": "bad"}',
        "summarize this",
    )

    assert response.tool_name == "summarize_text"
    assert response.tool_input == {}


def test_ollama_provider_converts_tool_input_values_to_strings() -> None:
    provider = OllamaModelProvider()

    response = provider._parse_response(  # noqa: SLF001 - parser regression test
        '{"thought": "use a tool", "tool_name": "summarize_text", "tool_input": {"text": 123}}',
        "summarize this",
    )

    assert response.tool_input == {"text": "123"}
