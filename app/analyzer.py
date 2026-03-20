from datetime import date, timedelta

THEME_KEYWORDS = {
    "load": ["负荷", "最大负荷", "平均负荷", "负载"],
    "energy": ["电量", "日电量", "月电量", "用电量"],
    "line_loss": ["线损", "线损率"],
}


def parse_time_range(question: str):
    today = date.today()
    q = question
    if "昨天" in q:
        d = today - timedelta(days=1)
        return {"mode": "day", "start": d.isoformat(), "end": d.isoformat(), "label": "昨天"}
    if "最近7天" in q or "近7天" in q:
        start = today - timedelta(days=6)
        return {"mode": "range", "start": start.isoformat(), "end": today.isoformat(), "label": "最近7天"}
    if "上月" in q:
        this_month = today.replace(day=1)
        end = this_month - timedelta(days=1)
        start = end.replace(day=1)
        return {"mode": "range", "start": start.isoformat(), "end": end.isoformat(), "label": "上月"}
    if "本月" in q:
        start = today.replace(day=1)
        return {"mode": "range", "start": start.isoformat(), "end": today.isoformat(), "label": "本月"}
    return {"mode": "range", "start": (today - timedelta(days=6)).isoformat(), "end": today.isoformat(), "label": "最近7天"}


def parse_theme(question: str):
    for theme, words in THEME_KEYWORDS.items():
        if any(w in question for w in words):
            return theme
    return "energy"


def parse_metric(question: str, theme: str):
    if theme == "load":
        if "平均" in question:
            return "avg_load"
        return "max_load"
    if theme == "line_loss":
        return "line_loss_rate"
    return "energy"


def parse_query_type(question: str):
    if any(k in question for k in ["同比", "环比", "对比"]):
        return "compare"
    if any(k in question for k in ["趋势", "变化"]):
        return "trend"
    if any(k in question for k in ["最高", "最大", "排行", "前", "TOP", "top"]):
        return "ranking"
    if any(k in question for k in ["多少", "总", "合计"]):
        return "summary"
    return "detail"


def parse_entity(question: str):
    if "供电所" in question:
        return "power_station"
    if "线路" in question:
        return "line"
    if "台区" in question:
        return "station_area"
    return "station_area"


def parse_region(question: str):
    common = ["全市", "城区", "城东", "城西", "城南", "城北"]
    for item in common:
        if item in question:
            return item
    return None


def parse_comparison(question: str):
    if "同比" in question:
        return "yoy"
    if "环比" in question:
        return "mom"
    return None


def analyze_question(question: str):
    theme = parse_theme(question)
    return {
        "theme": theme,
        "metric": parse_metric(question, theme),
        "query_type": parse_query_type(question),
        "entity": parse_entity(question),
        "time_range": parse_time_range(question),
        "region": parse_region(question),
        "comparison": parse_comparison(question),
        "question": question,
        "need_clarification": False,
    }
