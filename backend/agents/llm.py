import os
from typing import Type
from pydantic import BaseModel
from langchain_groq import ChatGroq

_llm: ChatGroq | None = None


def get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.1,
            api_key=os.environ["GROQ_KEY"],
        )
    return _llm


def get_structured_llm(output_schema: Type[BaseModel]):
    return get_llm().with_structured_output(output_schema)
