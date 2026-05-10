import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

RUNS_FILE = os.environ.get(
    "RUNS_INDEX_FILE",
    str(Path(__file__).parent.parent.parent / "data" / "runs.jsonl"),
)


def append_run(entry: dict[str, Any]) -> None:
    """Append a run summary to the index file. Adds `created_at` if absent."""
    entry = {**entry}
    entry.setdefault("created_at", datetime.utcnow().isoformat())
    Path(RUNS_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(RUNS_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def list_runs(limit: int = 10) -> list[dict]:
    """Return the most recent `limit` runs (newest first)."""
    path = Path(RUNS_FILE)
    if not path.exists():
        return []
    with open(path) as f:
        lines = f.readlines()
    runs = [json.loads(line) for line in lines if line.strip()]
    return list(reversed(runs))[:limit]
