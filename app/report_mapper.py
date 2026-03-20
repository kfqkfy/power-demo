from typing import Any, Dict, List

from metadata import load_metadata


SEMANTIC_TARGET_FIELDS = [
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


def load_mapping_config() -> Dict[str, Any]:
    meta = load_metadata()
    return meta.get("mappings", {})


def normalize_raw_row(raw_row: Dict[str, Any], source_table: str = "raw_unknown") -> Dict[str, Any]:
    """
    将 raw 层记录转换为统一 semantic 事实行。
    这里先做最小骨架：
    - 优先保留 raw 中已有 code/name 字段
    - 不强依赖行号
    - 为后续按 mapping 细化预留字段
    """
    return {
        "stat_month": raw_row.get("stat_month") or raw_row.get("stat_date") or raw_row.get("period"),
        "report_code": raw_row.get("report_code"),
        "report_name": raw_row.get("report_name"),
        "metric_code": raw_row.get("metric_code") or raw_row.get("indicator_code"),
        "metric_name": raw_row.get("metric_name") or raw_row.get("indicator_name"),
        "metric_group": raw_row.get("metric_group"),
        "time_scope": raw_row.get("time_scope") or raw_row.get("period_type"),
        "energy_type_lv1": raw_row.get("energy_type_lv1"),
        "energy_type_lv2": raw_row.get("energy_type_lv2"),
        "entity_code": raw_row.get("entity_code"),
        "entity_name": raw_row.get("entity_name"),
        "entity_level": raw_row.get("entity_level"),
        "parent_entity_code": raw_row.get("parent_entity_code") or raw_row.get("parent_code"),
        "parent_entity_name": raw_row.get("parent_entity_name") or raw_row.get("parent_name"),
        "category_code": raw_row.get("category_code"),
        "category_path": raw_row.get("category_path"),
        "value": raw_row.get("value"),
        "unit": raw_row.get("unit"),
        "source_table": source_table,
        "source_row_key": raw_row.get("source_row_key") or raw_row.get("id") or raw_row.get("row_key"),
    }


def build_semantic_rows(raw_rows: List[Dict[str, Any]], source_table: str) -> List[Dict[str, Any]]:
    rows = []
    for row in raw_rows:
        normalized = normalize_raw_row(row, source_table=source_table)
        rows.append({k: normalized.get(k) for k in SEMANTIC_TARGET_FIELDS})
    return rows
