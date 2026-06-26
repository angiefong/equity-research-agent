from pydantic import BaseModel

from backend.agents import llm


class FakeChatOpenAI:
    calls = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.structured = []
        FakeChatOpenAI.calls.append(kwargs)

    def with_structured_output(self, output_schema, method="function_calling"):
        self.structured.append((output_schema, method))
        return ("structured", output_schema, method, self)


class FakeChatGroq:
    calls = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        FakeChatGroq.calls.append(kwargs)

    def with_structured_output(self, output_schema, method="function_calling"):
        return ("structured-groq", output_schema, method, self)


class FakeSchema(BaseModel):
    value: str


def reset_llm_state():
    FakeChatOpenAI.calls = []
    FakeChatGroq.calls = []
    llm._openrouter_clients.clear()
    llm._openai_clients.clear()
    llm._groq_clients.clear()


def test_groq_client_uses_higher_retry_default(monkeypatch):
    reset_llm_state()
    monkeypatch.setattr(llm, "ChatGroq", FakeChatGroq)
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_KEY", "gsk-test-key")
    monkeypatch.delenv("LLM_MAX_RETRIES", raising=False)
    monkeypatch.delenv("GROQ_MAX_RETRIES", raising=False)

    client = llm.get_llm("large")

    assert isinstance(client, FakeChatGroq)
    assert FakeChatGroq.calls[0]["max_retries"] == 6


def test_provider_specific_retry_env_overrides_default(monkeypatch):
    reset_llm_state()
    monkeypatch.setattr(llm, "ChatGroq", FakeChatGroq)
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_KEY", "gsk-test-key")
    monkeypatch.setenv("GROQ_MAX_RETRIES", "9")

    llm.get_llm("small")

    assert FakeChatGroq.calls[0]["max_retries"] == 9


def test_openrouter_provider_uses_openai_compatible_client(monkeypatch):
    reset_llm_state()
    monkeypatch.setattr(llm, "ChatOpenAI", FakeChatOpenAI)
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-test-key")
    monkeypatch.setenv("OPENROUTER_MODEL_LARGE", "openai/gpt-4o")
    monkeypatch.setenv("OPENROUTER_HTTP_REFERER", "https://portfolio.example")
    monkeypatch.setenv("OPENROUTER_APP_TITLE", "Portfolio Research Demo")

    client = llm.get_llm("large")

    assert isinstance(client, FakeChatOpenAI)
    assert FakeChatOpenAI.calls == [
        {
            "model": "openai/gpt-4o",
            "temperature": 0.1,
            "api_key": "or-test-key",
            "max_retries": 6,
            "base_url": "https://openrouter.ai/api/v1",
            "default_headers": {
                "X-OpenRouter-Title": "Portfolio Research Demo",
                "HTTP-Referer": "https://portfolio.example",
            },
        }
    ]


def test_openrouter_structured_llm_uses_requested_method(monkeypatch):
    reset_llm_state()
    monkeypatch.setattr(llm, "ChatOpenAI", FakeChatOpenAI)
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-test-key")

    structured = llm.get_structured_llm(FakeSchema, method="json_mode", tier="small")

    assert structured[0] == "structured"
    assert structured[1] is FakeSchema
    assert structured[2] == "json_mode"
    assert structured[3].kwargs["model"] == "meta-llama/llama-3.1-8b-instruct"
