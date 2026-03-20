import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from analyzer import analyze_question
from llm_analyzer import analyze_with_llm
from sql_builder import build_sql
from compare_builder import build_compare_sql
from db import run_query
from metadata import load_metadata, save_json, ALLOWED_FILES
from semantic_parser import parse_question_rule, parse_question_llm
from metadata_retriever import retrieve_candidates
from query_planner import build_query_plan
from sql_compiler import compile_plan_to_sql
from report_mapper import build_semantic_rows, load_mapping_config

app = FastAPI(title="Power Data NL2SQL Demo", version="0.3.0")


class AskRequest(BaseModel):
    question: str
    use_llm: bool = False


class MetadataSaveRequest(BaseModel):
    section: str
    content: str


class RawPreviewRequest(BaseModel):
    source_table: str = "raw_demo"
    rows: list[dict]


def resolve_analysis(question: str, use_llm: bool):
    if use_llm or os.getenv("ANALYZER_MODE", "rule") == "llm":
        return analyze_with_llm(question)
    return analyze_question(question)


@app.get("/")
def index():
    return FileResponse("index.html")


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/themes")
def themes():
    return {
        "supported_themes": ["energy", "load", "line_loss"],
        "supported_queries": ["detail", "summary", "ranking", "compare"],
        "analyzer_modes": ["rule", "llm"],
        "default_analyzer_mode": os.getenv("ANALYZER_MODE", "rule"),
        "llm_model": os.getenv("LLM_MODEL", "gpt-5.4"),
        "examples": [
            "最近7天哪个台区最大负荷最高？",
            "最近7天哪个供电所最大负荷最高？",
            "本月各供电所总电量排行",
            "本月某线路下台区线损率情况",
            "本月城南台区线损率同比情况"
        ]
    }


@app.get("/metadata")
def metadata():
    return load_metadata()


@app.post("/metadata/save")
def metadata_save(req: MetadataSaveRequest):
    if req.section not in ALLOWED_FILES:
        raise HTTPException(status_code=400, detail="invalid metadata section")
    import json
    try:
        parsed = json.loads(req.content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"invalid json: {e}")
    save_json(ALLOWED_FILES[req.section], parsed)
    return {"ok": True, "section": req.section}


@app.post("/analyze")
def analyze(req: AskRequest):
    return resolve_analysis(req.question, req.use_llm)


@app.post("/raw/preview-semantic")
def raw_preview_semantic(req: RawPreviewRequest):
    config = load_mapping_config()
    rows = build_semantic_rows(req.rows, req.source_table)
    return {
        "mapping_config": config,
        "semantic_rows": rows,
        "count": len(rows),
    }


@app.post("/semantic/analyze")
def semantic_analyze(req: AskRequest):
    semantic = parse_question_llm(req.question) if req.use_llm else parse_question_rule(req.question)
    candidates = retrieve_candidates(semantic)
    plan = build_query_plan(semantic, candidates)
    sql, params = compile_plan_to_sql(plan)
    return {
        "semantic": semantic,
        "candidates": candidates,
        "plan": plan,
        "sql": sql,
        "params": params,
    }


@app.post("/ask")
def ask(req: AskRequest):
    semantic = parse_question_llm(req.question) if req.use_llm else parse_question_rule(req.question)
    candidates = retrieve_candidates(semantic)
    plan = build_query_plan(semantic, candidates)
    sql, params = compile_plan_to_sql(plan)
    rows = run_query(sql, params)

    if semantic.get("intent") == "ranking":
        if rows:
            answer = f"查询完成。当前排名第一的是 {rows[0]['entity_name']}，指标值为 {rows[0]['metric_value']}。"
        else:
            answer = "查询完成，但没有找到符合条件的数据。"
    elif semantic.get("intent") == "summary":
        value = rows[0]["metric_value"] if rows else None
        answer = f"查询完成。汇总结果为 {value}。"
    else:
        answer = f"查询完成，共返回 {len(rows)} 条记录。"

    return {
        "semantic": semantic,
        "candidates": candidates,
        "plan": plan,
        "sql": sql,
        "params": params,
        "rows": rows,
        "answer": answer,
    }
