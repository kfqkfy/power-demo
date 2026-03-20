import json
import os
from urllib import request

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://127.0.0.1:8848/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5.4")

SYSTEM_PROMPT = """
你是电力行业问题分析器。你的任务不是回答用户问题，而是把问题解析成结构化 json。
只输出 json，不要输出 markdown，不要解释。
字段固定为这个 json 对象：
{
  "theme": "energy|load|line_loss",
  "metric": "energy|max_load|avg_load|line_loss_rate",
  "query_type": "detail|summary|ranking|compare",
  "entity": "station_area|power_station|line",
  "time_range": {
    "mode": "day|range",
    "start": "YYYY-MM-DD",
    "end": "YYYY-MM-DD",
    "label": "原始时间短语"
  },
  "region": "全市|城区|城东|城西|城南|城北|null",
  "comparison": "yoy|mom|null",
  "question": "原问题",
  "need_clarification": false
}
如果无法确定，也要尽量给最合理结果，need_clarification 默认 false。
今天日期按 2026-03-18 处理。
""".strip()


def analyze_with_llm(question: str):
    payload = {
        "model": LLM_MODEL,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": SYSTEM_PROMPT}]},
            {"role": "user", "content": [{"type": "input_text", "text": question}]},
        ],
        "text": {"format": {"type": "json_object"}},
    }

    req = request.Request(
        f"{LLM_BASE_URL}/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}",
        },
        method="POST",
    )

    with request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    text = data.get("output_text")
    if not text:
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in ["output_text", "text"] and content.get("text"):
                    text = content.get("text")
                    break
            if text:
                break

    if not text:
        raise RuntimeError(f"LLM returned no text: {data}")

    return json.loads(text)
