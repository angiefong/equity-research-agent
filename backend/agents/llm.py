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

_groq_clients: dict[str, ChatGroq] = {}
_openai_clients: dict[str, ChatOpenAI] = {}


def _get_groq(tier: str) -> ChatGroq:
    if tier not in _groq_clients:
        _groq_clients[tier] = ChatGroq(
            model=_GROQ_MODELS[tier],
            temperature=0.1,
            api_key=os.environ["GROQ_KEY"],
        )
    return _groq_clients[tier]


def _get_openai(tier: str) -> ChatOpenAI:
    if tier not in _openai_clients:
        _openai_clients[tier] = ChatOpenAI(
            model=_OPENAI_MODELS[tier],
            temperature=0.1,
            api_key=os.environ["OPENAI_API_KEY"],
        )
    return _openai_clients[tier]


def _has_openai_fallback() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def get_llm(tier: str = "large"):
    primary = _get_groq(tier)
    if _has_openai_fallback():
        return primary.with_fallbacks([_get_openai(tier)])
    return primary


def get_structured_llm(
    output_schema: Type[BaseModel],
    method: str = "function_calling",
    tier: str = "large",
):
    primary = _get_groq(tier).with_structured_output(output_schema, method=method)
    if _has_openai_fallback():
        openai_method = method if method in ("function_calling", "json_mode", "json_schema") else "function_calling"
        fallback = _get_openai(tier).with_structured_output(output_schema, method=openai_method)
        return primary.with_fallbacks([fallback])
    return primary
