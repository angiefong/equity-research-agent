import os
from typing import Type
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

_GROQ_MODELS = {
    "large": "llama-3.3-70b-versatile",
    "small": "llama-3.1-8b-instant",
}

_OPENAI_MODELS = {
    "large": "gpt-4o",
    "small": "gpt-4o-mini",
}

_OPENROUTER_MODELS = {
    "large": "deepseek/deepseek-v4-flash",
    "small": "meta-llama/llama-3.1-8b-instruct",
}

_groq_clients: dict[str, ChatGroq] = {}
_openai_clients: dict[str, ChatOpenAI] = {}
_openrouter_clients: dict[str, ChatOpenAI] = {}


def _provider() -> str:
    return os.environ.get("LLM_PROVIDER", "groq").strip().lower()


def _env_model(prefix: str, tier: str, defaults: dict[str, str]) -> str:
    if tier not in defaults:
        raise ValueError(f"Unknown LLM tier: {tier}")
    return os.environ.get(f"{prefix}_MODEL_{tier.upper()}", defaults[tier])


def _get_groq(tier: str) -> ChatGroq:
    if tier not in _groq_clients:
        _groq_clients[tier] = ChatGroq(
            model=_env_model("GROQ", tier, _GROQ_MODELS),
            temperature=0.1,
            api_key=os.environ["GROQ_KEY"],
        )
    return _groq_clients[tier]


def _get_openai(tier: str) -> ChatOpenAI:
    if tier not in _openai_clients:
        _openai_clients[tier] = ChatOpenAI(
            model=_env_model("OPENAI", tier, _OPENAI_MODELS),
            temperature=0.1,
            api_key=os.environ["OPENAI_API_KEY"],
        )
    return _openai_clients[tier]


def _get_openrouter(tier: str) -> ChatOpenAI:
    if tier not in _openrouter_clients:
        headers = {"X-OpenRouter-Title": os.environ.get("OPENROUTER_APP_TITLE", "Equity Research Agent")}
        if referer := os.environ.get("OPENROUTER_HTTP_REFERER"):
            headers["HTTP-Referer"] = referer

        _openrouter_clients[tier] = ChatOpenAI(
            model=_env_model("OPENROUTER", tier, _OPENROUTER_MODELS),
            temperature=0.1,
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            default_headers=headers,
        )
    return _openrouter_clients[tier]


def _has_openai_fallback() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def get_llm(tier: str = "large"):
    if _provider() == "openrouter":
        return _get_openrouter(tier)
    if _provider() != "groq":
        raise ValueError("LLM_PROVIDER must be 'groq' or 'openrouter'")

    primary = _get_groq(tier)
    if _has_openai_fallback():
        return primary.with_fallbacks([_get_openai(tier)])
    return primary


def get_structured_llm(
    output_schema: Type[BaseModel],
    method: str = "function_calling",
    tier: str = "large",
):
    if _provider() == "openrouter":
        return _get_openrouter(tier).with_structured_output(output_schema, method=method)
    if _provider() != "groq":
        raise ValueError("LLM_PROVIDER must be 'groq' or 'openrouter'")

    primary = _get_groq(tier).with_structured_output(output_schema, method=method)
    if _has_openai_fallback():
        openai_method = method if method in ("function_calling", "json_mode", "json_schema") else "function_calling"
        fallback = _get_openai(tier).with_structured_output(output_schema, method=openai_method)
        return primary.with_fallbacks([fallback])
    return primary
