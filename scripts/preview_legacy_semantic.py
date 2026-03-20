#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
sys.path.insert(0, str(APP_DIR))

from report_mapper import build_semantic_rows  # noqa: E402

RAW_JSON_DEFAULT = ROOT / "localdata" / "raw_legacy_report.json"
OUT_JSON_DEFAULT = ROOT / "localdata" / "semantic_legacy_report.json"
SOURCE_TABLE_DEFAULT = "raw_legacy_report_private"


def main():
    raw_json = Path(sys.argv[1]) if len(sys.argv) > 1 else RAW_JSON_DEFAULT
    out_json = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT_JSON_DEFAULT
    source_table = sys.argv[3] if len(sys.argv) > 3 else SOURCE_TABLE_DEFAULT

    rows = json.loads(raw_json.read_text(encoding="utf-8"))
    semantic_rows = build_semantic_rows(rows, source_table=source_table)

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(semantic_rows, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"read {len(rows)} raw rows from {raw_json}")
    print(f"wrote {len(semantic_rows)} semantic rows to {out_json}")
    if semantic_rows:
        print(json.dumps(semantic_rows[:5], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
