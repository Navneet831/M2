import duckdb
import time
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import sqlglot
from sqlglot import exp
import uvicorn
import threading
import webbrowser
import logging
import os

# ==========================================================
# ENTERPRISE CONFIGURATION & GOVERNANCE
# ==========================================================
DB_PATH = os.getenv("DB_PATH", "warehouse.duckdb")
ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")]
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SemanticEngine")

app = FastAPI(title="L5 Enterprise Semantic Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Isolated DuckDB with strict SLA and Hardware Governance
try:
    con = duckdb.connect(DB_PATH, read_only=True)
    con.execute("PRAGMA threads=2")
    con.execute("PRAGMA memory_limit='2GB'")
    con.execute("PRAGMA enable_profiling='json'") # Enable telemetry
    logger.info(f"SUCCESS: Connected to {DB_PATH} with STRICT governance SLAs.")
except Exception as e:
    logger.fatal(f"FATAL ERROR: Could not connect to {DB_PATH}. {str(e)}")
    con = None

# ==========================================================
# SECURITY & POLICY ENFORCEMENT & AUDIT LOG
# ==========================================================
AUDIT_LOG = []

class GovernancePolicy:
    MAX_JOINS = 10
    ALLOWED_FUNCTIONS = {"SUM", "AVG", "MIN", "MAX", "COUNT", "CAST", "COALESCE", "NULLIF", "DATE_TRUNC", "ROW_NUMBER", "RANK", "DENSE_RANK", "LAG", "LEAD"}

    @classmethod
    def enforce(cls, ast: exp.Expression):
        join_count = 0

        for node in ast.walk():
            if isinstance(node, exp.Join):
                join_count += 1
                if join_count > cls.MAX_JOINS:
                    raise ValueError(f"Policy Violation: Query contains {join_count} joins. Maximum is {cls.MAX_JOINS}.")
            elif isinstance(node, exp.Func):
                func_name = node.sql_name().upper()
                if func_name not in cls.ALLOWED_FUNCTIONS and func_name != "":
                    AUDIT_LOG.append({"time": time.time(), "event": "NON_STANDARD_FUNC", "details": func_name})

# ==========================================================
# API PAYLOADS & AST PARSER
# ==========================================================
class SqlPayload(BaseModel):
    sql: str
    is_explain: bool = False

@app.post("/api/query/parse")
def parse_raw_sql_to_ui(payload: SqlPayload):
    """
    BIDIRECTIONAL AST ROUND-TRIPPING.
    Takes Raw SQL, builds the AST, and deconstructs it back into UI state blocks.
    """
    try:
        ast = sqlglot.parse_one(payload.sql, read="duckdb")

        ui_state = {
            "from": ast.args.get("from").this.name if ast.args.get("from") else "",
            "select": [{"col": e.sql(dialect="duckdb"), "agg": "NONE", "alias": e.alias_or_name, "is_expr": True} for e in ast.expressions],
            "where": [{"col": ast.args.get("where").this.sql(dialect="duckdb"), "op": "", "val": "", "logic": "AND"}] if ast.args.get("where") else [],
            "group_by": [{"col": g.sql(dialect="duckdb")} for g in ast.args.get("group").expressions] if ast.args.get("group") else [],
            "order_by": [{"col": o.this.sql(dialect="duckdb"), "dir": "DESC" if o.args.get("desc") else "ASC"} for o in ast.args.get("order").expressions] if ast.args.get("order") else [],
            "limit": int(ast.args.get("limit").expression.name) if ast.args.get("limit") else None,
            "distinct": True if ast.args.get("distinct") else False
        }
        return {"status": "success", "ui_state": ui_state}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.post("/api/query/compile_and_execute")
def compile_and_execute(req: SqlPayload):
    if not req.sql:
        raise HTTPException(status_code=400, detail="SQL cannot be empty")
    if not con: raise HTTPException(status_code=500, detail="Database Offline")

    pipeline_telemetry = {"parse_ms": 0, "policy_ms": 0, "execution_ms": 0}
    t0 = time.time()

    # Pass 1: Strict Syntax Validation via sqlglot
    try:
        ast = sqlglot.parse_one(req.sql, read="duckdb")
        pipeline_telemetry["parse_ms"] = round((time.time() - t0) * 1000, 2)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Syntax Parsing Error:\n{str(e)}")

    # Pass 2: Policy Enforcement
    t1 = time.time()
    try:
        GovernancePolicy.enforce(ast)
        pipeline_telemetry["policy_ms"] = round((time.time() - t1) * 1000, 2)
    except ValueError as ve:
        raise HTTPException(status_code=403, detail=str(ve))

    # Transpile to safe physical dialect
    final_sql = ast.sql(dialect="duckdb", pretty=True)
    AUDIT_LOG.append({"time": time.time(), "event": "EXECUTE", "details": final_sql})

    # Pass 3: Optimizer Introspection / EXPLAIN
    if req.is_explain:
        try:
            explain_plan = con.execute(f"EXPLAIN {final_sql}").fetchall()
            return {"type": "explain", "sql": final_sql, "plan": "\n".join([row[1] for row in explain_plan]), "telemetry": pipeline_telemetry}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"EXPLAIN Failed: {str(e)}")

    # Pass 4: Physical Execution
    t2 = time.time()
    try:
        df = con.execute(final_sql).fetchdf()
        pipeline_telemetry["execution_ms"] = round((time.time() - t2) * 1000, 2)
        df = df.where(pd.notnull(df), None)
        return {"type": "data", "sql": final_sql, "rows": df.to_dict(orient="records"), "columns": df.columns.tolist(), "telemetry": pipeline_telemetry, "row_count": len(df)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Execution Engine Error: {str(e)}")

# ==========================================================
# METADATA ENDPOINTS (100% Driven by DB metadata)
# ==========================================================
@app.get("/api/v1/schema")
def get_tables():
    if con:
        res = con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()
        return [r[0] for r in res]
    return []

@app.get("/api/metadata/schema/{table}")
def get_schema(table: str):
    if not con: raise HTTPException(status_code=500, detail="Database Offline")
    valid_tables = con.execute("SHOW TABLES").fetchdf().iloc[:, 0].tolist()
    if table not in valid_tables:
        raise HTTPException(status_code=404, detail="Table not found")
    table_escaped = table.replace('"', '""')
    return {"schema": con.execute(f'DESCRIBE "{table_escaped}"').fetchdf().to_dict(orient="records")}

@app.get("/api/metadata/audit")
def get_audit_log():
    return {"audit_log": AUDIT_LOG[::-1][:50]}

# ==========================================================
# FRONTEND INJECTION (Zero Node.js, 100% Vanilla JS)
# ==========================================================
@app.get("/", response_class=HTMLResponse)
def serve_ui():
    # Load HTML template from file
    html_path = os.path.join(os.path.dirname(__file__), "db_query_ui.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    print("\n[AST ENGINE] Launching L5 Semantic Layer on Localhost...\n")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")