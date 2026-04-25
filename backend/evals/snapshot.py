"""Epoch-scoped tool monkeypatch for deterministic eval replay.

Patches data-fetching functions in `backend/tools/*` so that the first run
in an epoch hits live APIs and writes fixtures to disk; subsequent runs
read the fixtures and skip the API calls. Patches at the tools layer (not
agents) so LLM calls in `backend/agents/*` continue to run live — those
are what the harness measures.
"""
from __future__ import annotations
import hashlib
import importlib
import json
import sys
import warnings
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Any, get_args, get_origin

from pydantic import BaseModel, TypeAdapter


# Args that vary by wall-clock and should be excluded from cache keys.
_TIME_VARYING_ARGS = {"as_of", "as_of_date", "now", "timestamp"}


def _arg_hash(args: tuple, kwargs: dict) -> str:
    """Stable hash of call args, ignoring time-varying kwargs."""
    filtered_kwargs = {k: v for k, v in sorted(kwargs.items()) if k not in _TIME_VARYING_ARGS}
    payload = json.dumps([list(args), filtered_kwargs], default=str, sort_keys=True)
    return hashlib.sha1(payload.encode()).hexdigest()[:16]


def _serialize(value: Any) -> dict:
    """Serialize a return value to a JSON-safe dict for fixture storage."""
    if isinstance(value, BaseModel):
        return {"_kind": "pydantic", "data": value.model_dump(mode="json")}
    if isinstance(value, list) and value and isinstance(value[0], BaseModel):
        return {"_kind": "list_pydantic", "data": [v.model_dump(mode="json") for v in value]}
    return {"_kind": "raw", "data": value}


def _deserialize(payload: dict, return_type: Any) -> Any:
    """Rehydrate a serialized fixture into the original return type."""
    kind = payload.get("_kind")
    data = payload.get("data")
    if kind == "raw":
        return data
    # Use TypeAdapter for both single Pydantic models and lists of them.
    return TypeAdapter(return_type).validate_python(data)


@contextmanager
def _patch(module_path: str, fn_name: str, fixture_dir: Path, return_type: Any | None = None):
    """Monkeypatch `module_path.fn_name` to read/write fixture files."""
    module = importlib.import_module(module_path)
    original = getattr(module, fn_name)

    # Best-effort: derive return type from annotation if not supplied.
    rt = return_type
    if rt is None:
        rt = original.__annotations__.get("return", dict)

    def wrapped(*args, **kwargs):
        key = _arg_hash(args, kwargs)
        fixture_path = fixture_dir / f"{fn_name}__{key}.json"
        if fixture_path.exists():
            payload = json.loads(fixture_path.read_text())
            return _deserialize(payload, rt)
        # Cold path
        result = original(*args, **kwargs)
        fixture_path.write_text(json.dumps(_serialize(result), indent=2))
        return result

    setattr(module, fn_name, wrapped)
    try:
        yield
    finally:
        setattr(module, fn_name, original)


# Patch targets — verified against backend/tools/ in the worktree.
_PATCH_TARGETS: list[tuple[str, str]] = [
    ("backend.tools.news",         "get_news_evidence"),
    ("backend.tools.market_data",  "get_market_data_evidence"),
    ("backend.tools.filings",      "fetch_recent_filings"),
    ("backend.tools.quant",        "compute_returns"),
    ("backend.tools.quant",        "compute_volatility"),
    ("backend.tools.quant",        "fetch_peer_comps"),
    ("backend.tools.quant",        "compute_pe_ratio"),
    ("backend.tools.quant",        "compute_ev_ebitda"),
    ("backend.tools.quant",        "generate_price_chart"),
]


@contextmanager
def epoch_snapshot(epoch: str, ticker: str, root: Path | None = None):
    """Activate snapshot replay for the duration of one ticker's pipeline run."""
    base = root if root is not None else Path("runtime_data/eval_fixtures")
    fixture_dir = base / epoch / ticker
    fixture_dir.mkdir(parents=True, exist_ok=True)

    with ExitStack() as stack:
        for module_path, fn_name in _PATCH_TARGETS:
            try:
                stack.enter_context(_patch(module_path, fn_name, fixture_dir))
            except (ImportError, AttributeError) as e:
                warnings.warn(
                    f"[snapshot] could not patch {module_path}.{fn_name}: {e}. "
                    f"Live API calls will be used for this tool.",
                    RuntimeWarning,
                )
        yield fixture_dir


def refresh_epoch(epoch: str) -> None:
    """CLI-callable: invalidate fixtures for an epoch by deleting the directory."""
    base = Path("runtime_data/eval_fixtures") / epoch
    if base.exists():
        import shutil
        shutil.rmtree(base)
        print(f"[snapshot] cleared {base}")
    else:
        print(f"[snapshot] no existing fixtures for epoch {epoch}")
    print(f"[snapshot] next eval run with --epoch={epoch} will re-populate from live APIs.")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(prog="python -m backend.evals.snapshot")
    sub = p.add_subparsers(dest="cmd", required=True)
    refresh = sub.add_parser("refresh", help="Clear fixtures for an epoch")
    refresh.add_argument("--epoch", required=True)
    args = p.parse_args()
    if args.cmd == "refresh":
        refresh_epoch(args.epoch)
