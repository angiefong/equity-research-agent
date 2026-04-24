import os
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver


def get_checkpointer() -> SqliteSaver:
    base = os.environ.get("RUNTIME_DATA_DIR", "./runtime_data")
    db_path = Path(base) / "checkpoints.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return SqliteSaver.from_conn_string(str(db_path))
