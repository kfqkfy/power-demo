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

RAW_VALUE_SPECS = [
    {
        "raw_key": "generation_total",
        "metric_suffix": "generation_total",
        "metric_name_suffix": "发电量(合计)",
        "metric_group": "generation",
        "time_scope": "current_month",
        "unit_default": "万千瓦时",
    },
    {
        "raw_key": "generation_trial",
        "metric_suffix": "generation_trial",
        "metric_name_suffix": "发电量(试运行)",
        "metric_group": "generation",
        "time_scope": "current_month",
        "unit_default": "万千瓦时",
    },
    {
        "raw_key": "grid_total",
        "metric_suffix": "grid_total",
        "metric_name_suffix": "上网电量(合计)",
        "metric_group": "grid",
        "time_scope": "current_month",
        "unit_default": "万千瓦时",
    },
    {
        "raw_key": "grid_trial",
        "metric_suffix": "grid_trial",
        "metric_name_suffix": "上网电量(试运行)",
        "metric_group": "grid",
        "time_scope": "current_month",
        "unit_default": "万千瓦时",
    },
]


def load_mapping_config() -> Dict[str, Any]:
    meta = load_metadata()
    return meta.get("mappings", {})


def clean_text(value: Any) -> Any:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return value


def build_metric_code(base_code: Any, metric_suffix: str) -> str:
    base = clean_text(base_code)
    if base:
        return f"{base}.{metric_suffix}"
    return metric_suffix


def build_metric_name(base_name: Any, suffix: str) -> str:
    base = clean_text(base_name)
    if base:
        return f"{base}-{suffix}"
    return suffix


def build_category_code(base_code: Any, metric_suffix: str) -> str:
    base = clean_text(base_code)
    if base:
        return f"{base}:{metric_suffix}"
    return metric_suffix


def build_category_path(entity_name: Any, metric_group: str, metric_name: str) -> str:
    parts = [clean_text(entity_name), metric_group, metric_name]
    return " / ".join([p for p in parts if p])


def base_semantic_row(raw_row: Dict[str, Any], source_table: str = "raw_unknown") -> Dict[str, Any]:
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


def expand_raw_value_rows(raw_row: Dict[str, Any], source_table: str) -> List[Dict[str, Any]]:
    raw_values = raw_row.get("raw_values") or {}
    expanded: List[Dict[str, Any]] = []
    base = base_semantic_row(raw_row, source_table=source_table)
    base_metric_code = base.get("metric_code")
    base_metric_name = base.get("metric_name")

    for spec in RAW_VALUE_SPECS:
        value = raw_values.get(spec["raw_key"])
        if value in (None, ""):
            continue

        row = dict(base)
        row["metric_code"] = build_metric_code(base_metric_code, spec["metric_suffix"])
        row["metric_name"] = build_metric_name(base_metric_name, spec["metric_name_suffix"])
        row["metric_group"] = spec["metric_group"]
        row["time_scope"] = spec["time_scope"]
        row["category_code"] = build_category_code(base_metric_code, spec["metric_suffix"])
        row["category_path"] = build_category_path(
            base.get("entity_name"), spec["metric_group"], row["metric_name"]
        )
        row["value"] = value
        row["unit"] = raw_row.get("unit") or spec["unit_default"]
        row["source_row_key"] = f"{base.get('source_row_key')}::{spec['metric_suffix']}"
        expanded.append({k: row.get(k) for k in SEMANTIC_TARGET_FIELDS})

    return expanded


def normalize_raw_row(raw_row: Dict[str, Any], source_table: str = "raw_unknown") -> Dict[str, Any]:
    return base_semantic_row(raw_row, source_table=source_table)


def build_semantic_rows(raw_rows: List[Dict[str, Any]], source_table: str) -> List[Dict[str, Any]]:
    rows = []
    for row in raw_rows:
        expanded = expand_raw_value_rows(row, source_table=source_table)
        if expanded:
            rows.extend(expanded)
            continue
        normalized = normalize_raw_row(row, source_table=source_table)
        rows.append({k: normalized.get(k) for k in SEMANTIC_TARGET_FIELDS})
    return rows
