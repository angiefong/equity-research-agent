import json
import os
from pathlib import Path
from typing import Optional

from backend.schemas.thesis import ThesisSnapshot


def _snapshot_dir(ticker: str) -> Path:
    base = os.environ.get("RUNTIME_DATA_DIR", "./runtime_data")
    return Path(base) / ticker.upper()


def save_snapshot(snapshot: ThesisSnapshot) -> Path:
    directory = _snapshot_dir(snapshot.ticker)
    directory.mkdir(parents=True, exist_ok=True)
    filename = directory / f"{snapshot.timestamp.strftime('%Y%m%dT%H%M%S')}_{snapshot.id[:8]}.json"
    filename.write_text(snapshot.model_dump_json(indent=2))
    return filename


def load_latest_snapshot(ticker: str) -> Optional[ThesisSnapshot]:
    directory = _snapshot_dir(ticker)
    if not directory.exists():
        return None
    files = sorted(directory.glob("*.json"))
    if not files:
        return None
    latest = files[-1]
    return ThesisSnapshot.model_validate_json(latest.read_text())
