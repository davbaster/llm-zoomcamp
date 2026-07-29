"""
dlt pipeline: load local Claude Code logs (raw JSON) into DuckDB.

Sources:
  - ~/.claude/projects/**/*.jsonl  -> table "session_events"
      One row per JSONL line (queue-operation, user, assistant, attachment, ...).
      The full parsed line is kept as a single raw JSON column ("event"),
      plus lightweight file-level metadata for filtering.
  - ~/.claude/history.jsonl        -> table "prompt_history"
      One row per submitted prompt (across all projects/sessions).

Both tables store the record as-is under a `json`-typed column so dlt does not
flatten/explode nested structures into child tables.

Usage:
    python pipeline.py
"""

import json
import os
from pathlib import Path

import dlt

CLAUDE_HOME = Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude"))
PROJECTS_DIR = CLAUDE_HOME / "projects"
HISTORY_FILE = CLAUDE_HOME / "history.jsonl"


def _iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            yield line_number, data


@dlt.resource(name="session_events", write_disposition="append", primary_key="_dlt_row_hash")
def session_events():
    if not PROJECTS_DIR.exists():
        return
    for project_dir in sorted(PROJECTS_DIR.iterdir()):
        if not project_dir.is_dir():
            continue
        for jsonl_file in sorted(project_dir.glob("*.jsonl")):
            session_id = jsonl_file.stem
            for line_number, event in _iter_jsonl(jsonl_file):
                yield {
                    "project": project_dir.name,
                    "session_id": session_id,
                    "source_file": str(jsonl_file),
                    "line_number": line_number,
                    "event_type": event.get("type"),
                    "event": event,
                }


session_events.apply_hints(columns={"event": {"data_type": "json"}})


@dlt.resource(name="prompt_history", write_disposition="append", primary_key="_dlt_row_hash")
def prompt_history():
    if not HISTORY_FILE.exists():
        return
    for line_number, entry in _iter_jsonl(HISTORY_FILE):
        yield {
            "line_number": line_number,
            "session_id": entry.get("sessionId"),
            "project": entry.get("project"),
            "timestamp": entry.get("timestamp"),
            "entry": entry,
        }


prompt_history.apply_hints(columns={"entry": {"data_type": "json"}})


@dlt.source(name="claude_logs")
def claude_logs():
    return [session_events(), prompt_history()]


if __name__ == "__main__":
    pipeline = dlt.pipeline(
        pipeline_name="claude_logs",
        destination="duckdb",
        dataset_name="claude_logs",
    )
    load_info = pipeline.run(claude_logs())
    print(load_info)

    with pipeline.sql_client() as client:
        for table in ("session_events", "prompt_history"):
            with client.execute_query(f"select count(*) from claude_logs.{table}") as cur:
                (count,) = cur.fetchone()
                print(f"{table}: {count} rows")
