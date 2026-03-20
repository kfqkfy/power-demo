#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pymysql

SCRIPT_PATH = Path(__file__).resolve()
ROOT = SCRIPT_PATH.parents[1] if len(SCRIPT_PATH.parents) > 1 else SCRIPT_PATH.parent
APP_DIR = ROOT / "app"
if not APP_DIR.exists():
    APP_DIR = SCRIPT_PATH.parent
sys.path.insert(0, str(APP_DIR))

from report_mapper import build_semantic_rows  # noqa: E402

RAW_JSON_DEFAULT = ROOT / "localdata" / "raw_legacy_report.json"
RAW_TABLE_DEFAULT = "raw_legacy_monthly_report"
SEMANTIC_TABLE_DEFAULT = "semantic_legacy_monthly_fact"
SCHEMA_FILE_DEFAULT = ROOT / "sql" / "raw_legacy_schema.sql"
if not SCHEMA_FILE_DEFAULT.exists():
    SCHEMA_FILE_DEFAULT = SCRIPT_PATH.parent.parent / "sql" / "raw_legacy_schema.sql"
if not SCHEMA_FILE_DEFAULT.exists():
    SCHEMA_FILE_DEFAULT = SCRIPT_PATH.parent / "raw_legacy_schema.sql"

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3307"))
DB_USER = os.getenv("DB_USER", "power")
DB_PASSWORD = os.getenv("DB_PASSWORD", "powerpass")
DB_NAME = os.getenv("DB_NAME", "power_demo")

RAW_INSERT_FIELDS = [
    "source_file_name",
    "source_report_type",
    "source_row_key",
    "report_code",
    "report_name",
    "stat_month",
    "metric_code",
    "metric_name",
    "entity_code",
    "entity_name",
    "entity_level",
    "parent_code",
    "parent_name",
    "time_scope",
    "value",
    "unit",
    "generation_total",
    "generation_trial",
    "grid_total",
    "grid_trial",
]

SEMANTIC_INSERT_FIELDS = [
    "stat_month",
    "report_code",
    "report_name",
    "metric_code",
    "metric_name",
    "metric_group",
    "time_scope",
    "energy_type_lv1",
    "energy_type_lv2",
    "entity_code",
    "entity_name",
    "entity_level",
    "parent_entity_code",
    "parent_entity_name",
    "category_code",
    "category_path",
    "value",
    "unit",
    "source_table",
    "source_row_key",
]


def get_conn():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
    )


def run_schema(conn, schema_path: Path):
    sql = schema_path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
            cur.execute(stmt)
    conn.commit()


def build_raw_insert_row(row: dict, source_file_name: str | None) -> dict:
    raw_values = row.get("raw_values") or {}
    return {
        "source_file_name": source_file_name,
        "source_report_type": "legacy_monthly_report",
        "source_row_key": row.get("source_row_key"),
        "report_code": row.get("report_code"),
        "report_name": row.get("report_name"),
        "stat_month": row.get("stat_month"),
        "metric_code": row.get("metric_code"),
        "metric_name": row.get("metric_name"),
        "entity_code": row.get("entity_code"),
        "entity_name": row.get("entity_name"),
        "entity_level": row.get("entity_level"),
        "parent_code": row.get("parent_code"),
        "parent_name": row.get("parent_name"),
        "time_scope": row.get("time_scope"),
        "value": row.get("value"),
        "unit": row.get("unit"),
        "generation_total": raw_values.get("generation_total"),
        "generation_trial": raw_values.get("generation_trial"),
        "grid_total": raw_values.get("grid_total"),
        "grid_trial": raw_values.get("grid_trial"),
    }


def bulk_upsert(conn, table_name: str, fields: list[str], rows: list[dict]):
    if not rows:
        return 0
    placeholders = ", ".join(["%s"] * len(fields))
    columns = ", ".join(fields)
    updates = ", ".join([f"{f}=VALUES({f})" for f in fields if f != "source_row_key"])
    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {updates}"
    payload = [tuple(row.get(f) for f in fields) for row in rows]
    with conn.cursor() as cur:
        cur.executemany(sql, payload)
    conn.commit()
    return len(rows)


def main():
    raw_json = Path(sys.argv[1]) if len(sys.argv) > 1 else RAW_JSON_DEFAULT
    source_file_name = sys.argv[2] if len(sys.argv) > 2 else raw_json.name

    raw_rows = json.loads(raw_json.read_text(encoding="utf-8"))
    semantic_rows = build_semantic_rows(raw_rows, source_table=RAW_TABLE_DEFAULT)
    raw_insert_rows = [build_raw_insert_row(row, source_file_name=source_file_name) for row in raw_rows]

    conn = get_conn()
    try:
        run_schema(conn, SCHEMA_FILE_DEFAULT)
        raw_count = bulk_upsert(conn, RAW_TABLE_DEFAULT, RAW_INSERT_FIELDS, raw_insert_rows)
        semantic_count = bulk_upsert(conn, SEMANTIC_TABLE_DEFAULT, SEMANTIC_INSERT_FIELDS, semantic_rows)
    finally:
        conn.close()

    print(f"loaded raw rows: {raw_count}")
    print(f"loaded semantic rows: {semantic_count}")


if __name__ == "__main__":
    main()
