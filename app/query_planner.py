def _score_candidate(semantic: dict, metric_candidate: dict, dimension_candidate: dict, join_candidate: dict) -> int:
    score = 0
    if metric_candidate:
        score += 50
    if dimension_candidate:
        score += 20
    if join_candidate and join_candidate.get("joins"):
        score += 20
    if semantic.get("time", {}).get("grain") == metric_candidate.get("grain"):
        score += 10
    return score



def build_query_plan(semantic: dict, candidates: dict) -> dict:
    metric_candidates = candidates.get("metric_candidates", [])
    if not metric_candidates:
        raise ValueError("no metric candidates matched")

    dimension = candidates.get("dimension_candidate") or {"table": "dim_station_area", "field": "station_area_name"}
    join_candidates = candidates.get("join_candidates", [])

    scored = []
    for idx, metric in enumerate(metric_candidates):
        join_candidate = join_candidates[idx] if idx < len(join_candidates) else {"joins": []}
        scored.append((
            _score_candidate(semantic, metric, dimension, join_candidate),
            metric,
            join_candidate,
        ))

    scored.sort(key=lambda x: x[0], reverse=True)
    _, metric, join_candidate = scored[0]

    return {
        "source_table": metric["table"],
        "metric_expr": metric["expr"],
        "time_field": metric["time_field"],
        "dimension_table": dimension["table"],
        "dimension_field": dimension["field"],
        "joins": join_candidate.get("joins", []),
        "filters": semantic.get("filters", []),
        "time": semantic.get("time", {}),
        "intent": semantic.get("intent", "summary"),
        "comparison": semantic.get("comparison"),
        "limit": semantic.get("limit", 10),
        "metric_name": (semantic.get("metrics") or [None])[0],
        "dimension_name": (semantic.get("dimensions") or ["station_area"])[0],
        "score": scored[0][0],
    }
