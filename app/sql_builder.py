from schema_registry import SCHEMA_REGISTRY


def build_sql(analysis: dict):
    registry = SCHEMA_REGISTRY[analysis["theme"]]
    table = registry["table"]
    date_field = registry["date_field"]
    entity = analysis.get("entity", "station_area")
    entity_field = registry["entity_fields"][entity]
    region_field = registry["region_field"]
    metric_field = registry["metric_fields"][analysis["metric"]]
    joins = registry.get("joins", [])

    from_clause = table
    for join in joins:
        from_clause += f" JOIN {join['table']} ON {join['on']}"

    where = [f"{table}.{date_field} BETWEEN :start_date AND :end_date"]
    params = {
        "start_date": analysis["time_range"]["start"],
        "end_date": analysis["time_range"]["end"],
    }

    if analysis.get("region") and analysis["region"] != "全市":
        where.append(f"{region_field} = :region")
        params["region"] = analysis["region"]

    if analysis["query_type"] == "ranking":
        agg = "MAX" if analysis["theme"] == "load" else "AVG"
        sql = f'''
        SELECT {entity_field} AS entity_name,
               {agg}({metric_field}) AS metric_value
        FROM {from_clause}
        WHERE {' AND '.join(where)}
        GROUP BY {entity_field}
        ORDER BY metric_value DESC
        LIMIT 10
        '''
        answer_hint = "ranking"
    elif analysis["query_type"] == "summary":
        agg = "SUM" if analysis["theme"] == "energy" else "AVG"
        if analysis.get("question") and any(k in analysis["question"] for k in ["各", "排行"]):
            sql = f'''
            SELECT {entity_field} AS entity_name,
                   {agg}({metric_field}) AS metric_value
            FROM {from_clause}
            WHERE {' AND '.join(where)}
            GROUP BY {entity_field}
            ORDER BY metric_value DESC
            LIMIT 20
            '''
            answer_hint = "summary_group"
        else:
            sql = f'''
            SELECT {agg}({metric_field}) AS metric_value
            FROM {from_clause}
            WHERE {' AND '.join(where)}
            '''
            answer_hint = "summary"
    elif analysis["query_type"] == "compare":
        sql = f'''
        SELECT {entity_field} AS entity_name,
               AVG({metric_field}) AS metric_value
        FROM {from_clause}
        WHERE {' AND '.join(where)}
        GROUP BY {entity_field}
        ORDER BY metric_value DESC
        LIMIT 20
        '''
        answer_hint = "compare"
    else:
        sql = f'''
        SELECT {table}.{date_field} AS stat_date,
               {entity_field} AS entity_name,
               {metric_field} AS metric_value
        FROM {from_clause}
        WHERE {' AND '.join(where)}
        ORDER BY {table}.{date_field} DESC
        LIMIT 20
        '''
        answer_hint = "detail"

    return sql.strip(), params, answer_hint
