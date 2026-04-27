import os
from contextlib import AbstractAsyncContextManager
from pathlib import Path

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


def get_checkpointer() -> AbstractAsyncContextManager[AsyncSqliteSaver]:
    base = os.environ.get("RUNTIME_DATA_DIR", "./runtime_data")
    db_path = Path(base) / "checkpoints.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return AsyncSqliteSaver.from_conn_string(str(db_path))
