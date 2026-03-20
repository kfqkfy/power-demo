import os
import time
from sqlalchemy import create_engine, text

DB_USER = os.getenv("DB_USER", "power")
DB_PASSWORD = os.getenv("DB_PASSWORD", "powerpass")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "power_demo")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"charset": "utf8mb4", "use_unicode": True, "init_command": "SET NAMES utf8mb4"},
)


def run_query(sql: str, params: dict):
    last_error = None
    for _ in range(10):
        try:
            with engine.connect() as conn:
                result = conn.execute(text(sql), params)
                return [dict(row._mapping) for row in result]
        except Exception as e:
            last_error = e
            time.sleep(2)
    raise last_error
