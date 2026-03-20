import json
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
METADATA_DIR = APP_DIR / "metadata"
ALLOWED_FILES = {"tables": "tables.json", "joins": "joins.json", "metrics": "metrics.json", "mappings": "mappings.json"}


def load_json(name: str):
    with open(METADATA_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(name: str, data):
    with open(METADATA_DIR / name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_metadata():
    return {
        "tables": load_json("tables.json"),
        "joins": load_json("joins.json"),
        "metrics": load_json("metrics.json"),
        "mappings": load_json("mappings.json") if (METADATA_DIR / "mappings.json").exists() else {},
    }
