from urllib import error as urlerror

from agentops_starter.models import ModelRequest, OllamaModelProvider


def test_ollama_provider_returns_actionable_error_when_unavailable(monkeypatch) -> None:
    def fail_urlopen(*_args, **_kwargs):
        raise urlerror.URLError("connection refused")

    monkeypatch.setattr("agentops_starter.models.urlrequest.urlopen", fail_urlopen)
    provider = OllamaModelProvider()

    response = provider.complete(ModelRequest(task="hello"))

    assert response.final_answer is not None
    assert "local model unavailable" in response.final_answer.lower()
