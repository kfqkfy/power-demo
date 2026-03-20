from metadata import load_metadata


FIELD_EXPR_BY_ROLE = {
    "energy": {"table": "energy_daily", "field": "energy_kwh", "default_agg": "SUM", "time_field": "stat_date", "entity_level": "station_area"},
    "max_load": {"table": "load_daily", "field": "max_load_kw", "default_agg": "MAX", "time_field": "stat_date", "entity_level": "station_area"},
    "avg_load": {"table": "load_daily", "field": "avg_load_kw", "default_agg": "AVG", "time_field": "stat_date", "entity_level": "station_area"},
    "line_loss_rate": {"table": "line_loss_daily", "field": "line_loss_rate", "default_agg": "AVG", "time_field": "stat_date", "entity_level": "station_area"},
}

DIMENSION_FIELD_MAP = {
    "station_area": "station_area_name",
    "line": "line_name",
    "power_station": "power_station_name",
    "region": "region_name",
}


def _find_metric_def(metrics_meta, metric_name):
    for item in metrics_meta:
        if item.get("metric") == metric_name:
            return item
    return None


def _find_dimension_table(tables_meta, dimension_name):
    field_name = DIMENSION_FIELD_MAP.get(dimension_name)
    if not field_name:
        return None
    for table in tables_meta:
        for field in table.get("fields", []):
            if field.get("name") == field_name:
                return {"table": table.get("table_name"), "field": field_name}
    return None


def _find_join_candidates(joins_meta, source_table, dimension_table):
    results = []
    for join in joins_meta:
        left_table = join.get("left_table")
        right_table = join.get("right_table")
        if left_table == source_table and right_table == dimension_table:
            on = join.get("on", "")
            alias_on = on.replace(dimension_table + ".", "sa.") if dimension_table == "dim_station_area" else on
            results.append({"table": source_table, "joins": [alias_on]})
    return results


def retrieve_candidates(semantic: dict) -> dict:
    meta = load_metadata()
    tables_meta = meta.get("tables", [])
    joins_meta = meta.get("joins", [])
    metrics_meta = meta.get("metrics", [])

    metric_name = (semantic.get("metrics") or [None])[0]
    dimension_name = (semantic.get("dimensions") or ["station_area"])[0]

    metric_def = _find_metric_def(metrics_meta, metric_name)
    field_expr = FIELD_EXPR_BY_ROLE.get(metric_name)
    if not metric_def or not field_expr:
        return {
            "metric_candidates": [],
            "dimension_candidate": None,
            "join_candidates": [],
        }

    metric_candidates = [{
        "table": field_expr["table"],
        "expr": f"{metric_def.get('aggregation', field_expr['default_agg'])}({field_expr['table']}.{field_expr['field']})",
        "time_field": f"{field_expr['table']}.{field_expr['time_field']}",
        "grain": semantic.get("time", {}).get("grain") or "day",
        "entity_level": field_expr["entity_level"],
        "metric_name": metric_name,
        "metric_desc": metric_def.get("desc"),
    }]

    dimension_candidate = _find_dimension_table(tables_meta, dimension_name)
    join_candidates = _find_join_candidates(joins_meta, field_expr["table"], (dimension_candidate or {}).get("table"))

    return {
        "metric_candidates": metric_candidates,
        "dimension_candidate": dimension_candidate,
        "join_candidates": join_candidates,
    }
