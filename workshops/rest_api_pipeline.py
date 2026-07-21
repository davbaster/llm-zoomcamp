"""
dlt pipeline: load Claude Code agent trace logs from the test-agent-traces-api
into DuckDB as raw JSON.

Source: https://test-agent-traces-api-xt2e7ottma-ew.a.run.app/docs
Endpoint: GET /logs (offset/limit pagination, max 1000 rows/page, no auth)

Each log entry is a Claude Code transcript-style JSON object (nested `message`,
`usage`, etc.). It is stored as a single `json`-typed column ("log") so dlt does
not flatten/explode the nested structure into child tables, plus a few
top-level columns (index, uuid, session_id, type, timestamp) for filtering.

Usage:
    uv run python rest_api_pipeline.py          # one page, 1000 records
    uv run python rest_api_pipeline.py --full   # 20 pages, 20,000 records
"""

import argparse

import dlt
from dlt.extract.source import DltSource
from dlt.hub import run
from dlt.hub.run import trigger
from dlt.sources.rest_api import RESTAPIConfig, rest_api_source

BASE_URL = "https://test-agent-traces-api-xt2e7ottma-ew.a.run.app/"


def _wrap_log(record: dict) -> dict:
    return {
        "index": record.get("index"),
        "uuid": record.get("uuid"),
        "session_id": record.get("sessionId"),
        "type": record.get("type"),
        "timestamp": record.get("timestamp"),
        "log": record,
    }


def agent_traces_source(base_url: str = BASE_URL) -> DltSource:
    config: RESTAPIConfig = {
        "client": {
            "base_url": base_url,
        },
        "resource_defaults": {
            "primary_key": "index",
            "write_disposition": "merge",
        },
        "resources": [
            {
                "name": "logs",
                "endpoint": {
                    "path": "logs",
                    "params": {
                        "limit": 1000,
                    },
                    "data_selector": "logs",
                    "paginator": {
                        "type": "offset",
                        "limit": 1000,
                        "total_path": "total",
                    },
                },
                "processing_steps": [
                    {"map": _wrap_log},
                ],
            },
        ],
    }
    source = rest_api_source(config, name="agent_traces")
    source.resources["logs"].apply_hints(columns={"log": {"data_type": "json"}})
    return source


@run.pipeline("agent_traces", trigger=trigger.schedule("0 12 * * *"))
def ingest_agent_traces(pages: int = 20) -> None:
    """Load `pages` x 1000 rows/page (API max) from /logs into DuckDB. Defaults to the full 20k-row sample."""
    pipeline = dlt.pipeline(
        pipeline_name="agent_traces",
        #destination="duckdb",
        destination="playground",
        dataset_name="agent_logs",
    )

    load_info = pipeline.run(agent_traces_source().add_limit(pages))
    print(load_info)

    with pipeline.sql_client() as client:
        with client.execute_query("select count(*) from agent_logs.logs") as cur:
            (count,) = cur.fetchone()
            print(f"logs: {count} rows")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--full",
        action="store_true",
        help="load 20 pages (20,000 records) instead of a single 1,000-record page",
    )
    args = parser.parse_args()
    ingest_agent_traces(pages=20 if args.full else 1)
