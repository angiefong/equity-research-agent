from typing import TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def dedupe_by_id(existing: list[T], new: list[T]) -> list[T]:
    seen_ids = {item.id for item in existing}
    merged = list(existing)
    for item in new:
        if item.id not in seen_ids:
            merged.append(item)
            seen_ids.add(item.id)
    return merged
