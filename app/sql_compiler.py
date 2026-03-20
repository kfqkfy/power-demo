def compile_plan_to_sql(plan: dict):
    source_table = plan["source_table"]
    metric_expr = plan["metric_expr"]
    time_field = plan["time_field"]
    dim_table = plan["dimension_table"]
    dim_field = plan["dimension_field"]
    joins = plan.get("joins", [])
    intent = plan.get("intent")
    limit = plan.get("limit", 10)

    params = {}
    join_sql = ""
    alias = "d"
    if dim_table == "dim_station_area":
        alias = "sa"
    if joins:
        join_sql = f" JOIN {dim_table} {alias} ON " + " AND ".join(joins)

    where_clauses = []
    time_cfg = plan.get("time", {})
    if time_cfg.get("start") and time_cfg.get("end"):
        where_clauses.append(f"{time_field} BETWEEN :start_date AND :end_date")
        params["start_date"] = time_cfg["start"]
        params["end_date"] = time_cfg["end"]

    where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    if intent == "ranking":
        sql = f"""
SELECT {alias}.{dim_field} AS entity_name,
       {metric_expr} AS metric_value
FROM {source_table}{join_sql}
{where_sql}
GROUP BY {alias}.{dim_field}
ORDER BY metric_value DESC
LIMIT {int(limit)}
        """.strip()
    elif intent == "summary":
        sql = f"""
SELECT {metric_expr} AS metric_value
FROM {source_table}{join_sql}
{where_sql}
        """.strip()
    else:
        sql = f"""
SELECT {alias}.{dim_field} AS entity_name,
       {metric_expr} AS metric_value
FROM {source_table}{join_sql}
{where_sql}
GROUP BY {alias}.{dim_field}
LIMIT {int(limit)}
        """.strip()

    return sql, params
