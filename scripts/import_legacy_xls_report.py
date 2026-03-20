#!/usr/bin/env python3
from __future__ import annotations

import json
import struct
from pathlib import Path
import sys

import olefile


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH_DEFAULT = ROOT / "localdata" / "private_report.xls"
OUT_JSON_DEFAULT = ROOT / "localdata" / "raw_legacy_report.json"


def parse_label(payload: bytes):
    row, col, xf = struct.unpack_from("<HHH", payload, 0)
    strlen = struct.unpack_from("<H", payload, 6)[0]
    flags = payload[8]
    if flags & 0x01:
        text = payload[9:9 + strlen * 2].decode("utf-16le", errors="ignore")
    else:
        text = payload[9:9 + strlen].decode("latin1", errors="ignore")
    return row, col, text


def parse_number(payload: bytes):
    row, col, xf = struct.unpack_from("<HHH", payload, 0)
    val = struct.unpack_from("<d", payload, 6)[0]
    return row, col, val


def parse_rk(payload: bytes):
    row, col, xf, rk = struct.unpack_from("<HHHI", payload, 0)
    mult100 = rk & 1
    is_int = rk & 2
    if is_int:
        value = rk >> 2
    else:
        raw = struct.pack("<I", rk & 0xFFFFFFFC) + b"\x00\x00\x00\x00"
        value = struct.unpack("<d", raw)[0]
    if mult100:
        value /= 100.0
    return row, col, value


def read_cells(report_path: str):
    ole = olefile.OleFileIO(report_path)
    data = ole.openstream("Workbook").read()
    cells = {}
    pos = 0
    while pos + 4 <= len(data):
        rt, ln = struct.unpack_from("<HH", data, pos)
        payload = data[pos + 4:pos + 4 + ln]
        try:
            if rt == 0x0204:  # LABEL
                r, c, v = parse_label(payload)
                cells[(r, c)] = v
            elif rt == 0x0203:  # NUMBER
                r, c, v = parse_number(payload)
                cells[(r, c)] = v
            elif rt == 0x027E:  # RK
                r, c, v = parse_rk(payload)
                cells[(r, c)] = v
        except Exception:
            pass
        pos += 4 + ln
    return cells


def clean_name(name: str | None) -> str | None:
    if name is None:
        return None
    return str(name).strip().replace("\u3000", " ")


def infer_level(name: str | None) -> str:
    if not name:
        return "unknown"
    stripped = clean_name(name) or ""
    if stripped == "总计":
        return "summary"
    if stripped.startswith("其中") or stripped.startswith("其中:") or stripped.startswith("其中："):
        return "subitem"
    if any(k in stripped for k in ["公司", "电厂", "电站", "热电", "发电厂"]):
        return "plant"
    return "category"


def build_raw_rows(cells: dict):
    report_name = clean_name(cells.get((4, 0)))
    report_code = clean_name(cells.get((5, 0)))
    year = clean_name(cells.get((7, 0)))
    month = clean_name(cells.get((7, 2)))
    stat_month = f"{year}-{str(month).zfill(2)}" if year and month else None

    rows = []
    current_parent_code = None
    current_parent_name = None

    for r in range(17, 1252):
        metric_name = clean_name(cells.get((r, 0)))
        metric_code = clean_name(cells.get((r, 1)))
        if not metric_name and not metric_code:
            continue

        level = infer_level(metric_name)
        if level in ("summary", "category"):
            current_parent_code = metric_code
            current_parent_name = metric_name

        rows.append({
            "source_row_key": f"row-{r}",
            "report_code": report_code,
            "report_name": report_name,
            "stat_month": stat_month,
            "metric_code": metric_code,
            "metric_name": metric_name,
            "entity_code": metric_code,
            "entity_name": metric_name,
            "entity_level": level,
            "parent_code": None if level in ("summary", "category") else current_parent_code,
            "parent_name": None if level in ("summary", "category") else current_parent_name,
            "time_scope": "current_month",
            "value": cells.get((r, 11)) if cells.get((r, 11)) not in (None, "") else cells.get((r, 5)),
            "unit": "万千瓦时",
            "raw_values": {
                "generation_total": cells.get((r, 5)),
                "generation_trial": cells.get((r, 6)),
                "grid_total": cells.get((r, 11)),
                "grid_trial": cells.get((r, 12)),
            }
        })
    return rows


def main():
    report_path = Path(sys.argv[1]) if len(sys.argv) > 1 else REPORT_PATH_DEFAULT
    out_json = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT_JSON_DEFAULT

    cells = read_cells(str(report_path))
    rows = build_raw_rows(cells)

    out_path = out_json
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"wrote {len(rows)} rows to {out_path}")
    if rows:
        print(json.dumps(rows[:5], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
