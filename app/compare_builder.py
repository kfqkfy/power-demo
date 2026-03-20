from datetime import datetime
from schema_registry import SCHEMA_REGISTRY


def shift_period(start: str, end: str, comparison: str):
    s = datetime.strptime(start, "%Y-%m-%d")
    e = datetime.strptime(end, "%Y-%m-%d")
    if comparison == "yoy":
        return s.replace(year=s.year - 1).strftime("%Y-%m-%d"), e.replace(year=e.year - 1).strftime("%Y-%m-%d")
    if comparison == "mom":
        # 简化处理：减 30 天
        from datetime import timedelta
        return (s - timedelta(days=30)).strftime("%Y-%m-%d"), (e - timedelta(days=30)).strftime("%Y-%m-%d")
    return None, None


def build_compare_sql(analysis: dict):
    registry = SCHEMA_REGISTRY[analysis["theme"]]
    table = registry["table"]
    date_field = registry["date_field"]
    entity = analysis.get("entity", "station_area")
    entity_field = registry["entity_fields"][entity]
    region_field = registry["region_field"]
    metric_field = registry["metric_fields"][analysis["metric"]]
    joins = registry.get("joins", [])

    prev_start, prev_end = shift_period(
        analysis["time_range"]["start"],
        analysis["time_range"]["end"],
        analysis.get("comparison") or "yoy",
    )

    from_clause = table
    for join in joins:
        from_clause += f" JOIN {join['table']} ON {join['on']}"

    current_where = [f"{table}.{date_field} BETWEEN :start_date AND :end_date"]
    prev_where = [f"{table}.{date_field} BETWEEN :prev_start_date AND :prev_end_date"]
    params = {
        "start_date": analysis["time_range"]["start"],
        "end_date": analysis["time_range"]["end"],
        "prev_start_date": prev_start,
        "prev_end_date": prev_end,
    }

    if analysis.get("region") and analysis["region"] != "全市":
        current_where.append(f"{region_field} = :region")
        prev_where.append(f"{region_field} = :region")
        params["region"] = analysis["region"]

    sql = f'''
    SELECT cur.entity_name,
           cur.metric_value AS current_value,
           prev.metric_value AS previous_value,
           CASE
             WHEN prev.metric_value IS NULL OR prev.metric_value = 0 THEN NULL
             ELSE ROUND((cur.metric_value - prev.metric_value) / prev.metric_value, 4)
           END AS change_rate
    FROM (
      SELECT {entity_field} AS entity_name,
             AVG({metric_field}) AS metric_value
      FROM {from_clause}
      WHERE {' AND '.join(current_where)}
      GROUP BY {entity_field}
    ) cur
    LEFT JOIN (
      SELECT {entity_field} AS entity_name,
             AVG({metric_field}) AS metric_value
      FROM {from_clause}
      WHERE {' AND '.join(prev_where)}
      GROUP BY {entity_field}
    ) prev
      ON cur.entity_name = prev.entity_name
    ORDER BY cur.metric_value DESC
    LIMIT 20
    '''

    return sql.strip(), params
