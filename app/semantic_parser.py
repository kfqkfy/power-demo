from datetime import date
from calendar import monthrange
import requests


def _month_bounds(today=None):
    today = today or date.today()
    start = today.replace(day=1)
    end = today.replace(day=monthrange(today.year, today.month)[1])
    return start.isoformat(), end.isoformat()


def parse_question_rule(question: str) -> dict:
    q = question.strip()
    start_date, end_date = _month_bounds()

    semantic = {
        "raw_question": q,
        "intent": "summary",
        "metrics": [],
        "dimensions": [],
        "filters": [],
        "time": {
            "grain": "day",
            "range_type": None,
            "start": None,
            "end": None,
            "label": None,
        },
        "comparison": None,
        "limit": 10,
    }

    if "排行" in q or "前十" in q or "top" in q.lower():
        semantic["intent"] = "ranking"
    elif "同比" in q or "环比" in q:
        semantic["intent"] = "compare"

    if "线损" in q:
        semantic["metrics"].append("line_loss_rate")
    if "负荷" in q:
        semantic["metrics"].append("max_load")
    if "电量" in q:
        semantic["metrics"].append("energy")

    if "线路" in q:
        semantic["dimensions"].append("line")
    elif "供电所" in q:
        semantic["dimensions"].append("power_station")
    elif "区域" in q:
        semantic["dimensions"].append("region")
    elif "台区" in q:
        semantic["dimensions"].append("station_area")

    if "本月" in q:
        semantic["time"] = {
            "grain": "month",
            "range_type": "current_month",
            "start": start_date,
            "end": end_date,
            "label": "本月",
        }

    if "同比" in q:
        semantic["comparison"] = "yoy"
    elif "环比" in q:
        semantic["comparison"] = "mom"

    return semantic


def parse_question_llm(question: str, model_url: str = "http://host.docker.internal:8848/v1/responses", api_key: str = "sk-RKk9oVy8cAQqirZfvuqazisnENaz9CweGUq9suwFfTAk4") -> dict:
    prompt = f"""
你是电力数据查询语义解析器。请把用户问题解析为 JSON，不要输出解释。
字段：intent, metrics, dimensions, filters, time, comparison, limit。
intent 只允许：summary, ranking, compare, detail
metrics 只填数组，可选：energy, max_load, avg_load, line_loss_rate
dimensions 只填数组，可选：station_area, line, power_station, region
comparison 可选：null, yoy, mom
用户问题：{question}
"""
    try:
        resp = requests.post(
            model_url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-5.4",
                "input": prompt,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data.get("output", [{}])[0].get("content", [{}])[0].get("text", "")
        import json
        parsed = json.loads(text)
        parsed["raw_question"] = question
        return parsed
    except Exception:
        return parse_question_rule(question)
