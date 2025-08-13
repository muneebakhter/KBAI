from __future__ import annotations

import os
import secrets
import time
import asyncio
from pathlib import Path
import json
import uuid
import mimetypes
from typing import Dict, List, Optional, Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile, Query, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, StreamingResponse, FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

from dotenv import load_dotenv

# Import our modules
from .storage import DB
from .auth import make_session, issue_token, authenticate_user, get_current_session, require_scopes
from .deps import get_current_auth, require_scopes_unified, KBAI_API_TOKEN
from .models import (
    TokenRequest, TokenResponse, TracesResponse, TraceItem, MetricsSummary,
    Project, FAQ, KBArticle, BatchFAQUpsertRequest, BatchKBUpsertRequest, 
    QueryRequest, QueryResponse, AuthModes, HealthStatus
)
from .middleware import TraceMiddleware

# Import AI worker functionality
try:
    from .ai_worker import AIWorker, QueryRequest as AIQueryRequest, QueryResponse as AIQueryResponse
    from .ai_worker import Source, ToolUsage, FAQCreateRequest, KBArticleCreateRequest, DocumentUploadResponse, IndexBuildResponse
    AI_WORKER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AI Worker functionality not available: {e}")
    AI_WORKER_AVAILABLE = False

APP_DIR = Path(__file__).resolve().parent
# Use data directory in project root for project mapping
PROJECT_ROOT = APP_DIR.parent
DATA_DIR_ROOT = PROJECT_ROOT / "data"
DATA_DIR_ROOT.mkdir(parents=True, exist_ok=True)
PROJ_MAP_FILE = DATA_DIR_ROOT / "proj_mapping.txt"
# Keep logs in HOME as before
HOME_ROOT = Path.home()
LOG_DIR = HOME_ROOT / ".kbai"
LOG_DIR.mkdir(parents=True, exist_ok=True)
REQUEST_LOG = LOG_DIR / "requests.jsonl"

load_dotenv(dotenv_path=APP_DIR.parent / ".env", override=False)

# Environment variables
def env(name: str, default: Optional[str]=None) -> str:
    return os.getenv(name, default)

# Use SQLite database in app directory
TRACE_DB_PATH = env("TRACE_DB_PATH", "./app/kbai_api.db")
MAX_REQUEST_BYTES = int(env("MAX_REQUEST_BYTES","65536"))
ALLOWED_ORIGINS = [o.strip() for o in env("ALLOWED_ORIGINS","*").split(",")]
SECURE_TOKEN = os.environ.get("KBAI_API_TOKEN") or secrets.token_hex(16)

TITLE = "Knowledge Base AI API"
VERSION = "1.0.0"

app = FastAPI(
    title=TITLE, 
    version=VERSION,
    openapi_tags=[
        {"name": "Auth", "description": "Authentication endpoints"},
        {"name": "Test", "description": "Testing endpoints"},
        {"name": "Projects", "description": "Project management"},
        {"name": "FAQs", "description": "FAQ management"},
        {"name": "Knowledge Base", "description": "Knowledge base management"},
        {"name": "Documents", "description": "Document upload and processing"},
        {"name": "AI Query", "description": "AI-powered query processing"},
        {"name": "Indexes", "description": "Index management"},
        {"name": "Tools", "description": "AI tool execution"},
    ],
    # Hide admin/observability endpoints from docs
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)
app.state.db = DB(TRACE_DB_PATH)
app.state.startup_time = time.time()  # Track startup time for uptime calculation

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tracing middleware (log every request/response)
app.add_middleware(TraceMiddleware, db=app.state.db, max_request_bytes=MAX_REQUEST_BYTES)

templates = Jinja2Templates(directory=str(APP_DIR / "templates"))
security = HTTPBearer(auto_error=False)

# Prometheus metrics
REQUEST_COUNT = Counter("kbai_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("kbai_request_latency_seconds", "Request latency", ["endpoint"])
READY_GAUGE = Gauge("kbai_ready", "Readiness state (1 ready, 0 not)")

# Data directory for project storage - use same location as project mapping
DATA_DIR = DATA_DIR_ROOT
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Initialize AI Worker if available (after DATA_DIR is defined)
if AI_WORKER_AVAILABLE:
    try:
        app.state.ai_worker = AIWorker(base_dir=str(DATA_DIR))
        print("✅ AI Worker initialized successfully")
    except Exception as e:
        print(f"⚠️ Failed to initialize AI Worker: {e}")
        app.state.ai_worker = None
else:
    app.state.ai_worker = None

def _project_dir(project_id: str) -> Path:
    d = DATA_DIR / project_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "faqs").mkdir(exist_ok=True)
    (d / "kb").mkdir(exist_ok=True)
    (d / "ingest").mkdir(exist_ok=True)
    return d

def _init_project_files(project_id: str) -> None:
    """Initialize empty FAQ and KB files for a new project"""
    project_dir = DATA_DIR / project_id
    
    # Create empty FAQ file if it doesn't exist
    faq_file = project_dir / f"{project_id}.faq.json"
    if not faq_file.exists():
        faq_file.write_text("[]", encoding="utf-8")
    
    # Create empty KB file if it doesn't exist
    kb_file = project_dir / f"{project_id}.kb.json"
    if not kb_file.exists():
        kb_file.write_text("[]", encoding="utf-8")
        
    # Create attachments directory
    (project_dir / "attachments").mkdir(exist_ok=True)

def _read_proj_map() -> Dict[str, Project]:
    mapping: Dict[str, Project] = {}
    if PROJ_MAP_FILE.exists():
        for line in PROJ_MAP_FILE.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            parts = line.split("|", 2)
            if len(parts) == 3:
                pid, name, active_str = parts
                mapping[pid] = Project(id=pid, name=name, active=(active_str == "1"))
    return mapping

def _write_proj_map(mapping: Dict[str, Project]) -> None:
    tmp = PROJ_MAP_FILE.with_suffix(".tmp")
    content = "\n".join(f"{p.id}|{p.name}|{'1' if p.active else '0'}" for p in mapping.values())
    tmp.write_text(content + "\n", encoding="utf-8")
    tmp.replace(PROJ_MAP_FILE)

def _list_json(dir_path: Path) -> List[dict]:
    items: List[dict] = []
    for file in sorted(dir_path.glob("*.json")):
        try:
            items.append(json.loads(file.read_text(encoding="utf-8")))
        except Exception:
            continue
    return items

def _write_json(file_path: Path, obj: dict) -> None:
    file_path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def _delete_json(file_path: Path) -> None:
    if file_path.exists():
        file_path.unlink()

def track_metrics(endpoint: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                response = await func(*args, **kwargs)
                status = getattr(response, "status_code", 200)
                return response
            except HTTPException as exc:
                status = exc.status_code
                raise
            finally:
                REQUEST_COUNT.labels("ANY", endpoint, str(locals().get("status", 200))).inc()
                REQUEST_LATENCY.labels(endpoint).observe(time.perf_counter() - start)
        return wrapper
    return decorator

@app.get("/healthz", response_class=PlainTextResponse, include_in_schema=False)
async def healthz():
    return "ok"

@app.get("/readyz", response_class=PlainTextResponse, include_in_schema=False)
async def readyz():
    # Check database connectivity
    try:
        app.state.db.query("SELECT 1")
        ready = True
    except Exception:
        ready = False
    READY_GAUGE.set(1 if ready else 0)
    return "ready" if ready else "not ready"

@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Authentication endpoints
@app.get("/v1/auth/modes", response_model=AuthModes, tags=["Auth"])
async def get_auth_modes():
    """Get available authentication modes."""
    return AuthModes(
        jwt_enabled=True,
        api_key_enabled=True,
        api_key_configured=bool(KBAI_API_TOKEN)
    )

@app.post("/v1/auth/token", response_model=TokenResponse, tags=["Auth"])
async def create_token(req: TokenRequest):
    # Authenticate user with username/password
    if not authenticate_user(req.username, req.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create session with appropriate scopes
    sess = make_session(req.client_name, req.scopes, req.ttl_seconds, None)
    out = issue_token(app.state.db, sess)
    return TokenResponse(
        access_token=out["token"], 
        expires_at=out["expires_at"], 
        session_id=out["session_id"]
    )

# Test endpoint
@app.get("/v1/test/ping", tags=["Test"])
async def ping(request: Request, auth: dict = Depends(get_current_auth), echo: Optional[str]=Query(None)):
    from datetime import datetime, timezone
    return {
        "ok": True,
        "pong": datetime.now(timezone.utc).isoformat(),
        "echo": echo,
        "auth_method": auth.get("auth_method"),
        "trace_id": "see /v1/traces"
    }

# Observability endpoints
@app.get("/v1/traces", response_model=TracesResponse, tags=["Observability"], include_in_schema=False)
async def list_traces(
    request: Request,
    auth: dict = Depends(get_current_auth),
    since: Optional[str] = Query(None, description="ISO timestamp"),
    limit: int = Query(100, ge=1, le=1000),
    status_code: Optional[int] = Query(None, ge=100, le=599),
    path: Optional[str] = Query(None, description="Path substring filter"),
    ip: Optional[str] = Query(None),
    has_error: Optional[bool] = Query(None, description="Filter by error presence"),
    since_seconds: Optional[int] = Query(None, description="Filter traces from N seconds ago"),
):
    # Check if user has required scopes (API key users have full access)
    if auth.get("auth_method") == "jwt":
        scopes = auth.get("scopes", [])
        if "read:basic" not in scopes and "read:traces" not in scopes:
            raise HTTPException(status_code=403, detail="insufficient permissions")
    
    rows = app.state.db.list_traces(
        since=since, 
        limit=limit, 
        status=status_code, 
        path=path, 
        ip=ip,
        has_error=has_error,
        since_seconds=since_seconds
    )
    items = []
    for r in rows:
        items.append(TraceItem(
            id=r["id"], ts=r["ts"], method=r["method"], path=r["path"],
            status=r["status"], latency_ms=r["latency_ms"], ip=r["ip"], ua=r["ua"],
            headers_slim=(json.loads(r["headers_slim"]) if r["headers_slim"] else None),
            query=(json.loads(r["query"]) if r["query"] else None),
            body_sha256=r["body_sha256"], token_sub=r["token_sub"], error=r["error"]
        ))
    return TracesResponse(items=items, next_cursor=None)

@app.get("/v1/traces/{trace_id}", response_model=TraceItem, tags=["Observability"], include_in_schema=False)
async def get_trace(
    trace_id: str,
    request: Request,
    auth: dict = Depends(get_current_auth)
):
    """Get a single trace by ID."""
    # Check if user has required scopes (API key users have full access)
    if auth.get("auth_method") == "jwt":
        scopes = auth.get("scopes", [])
        if "read:basic" not in scopes and "read:traces" not in scopes:
            raise HTTPException(status_code=403, detail="insufficient permissions")
    
    row = app.state.db.get_trace_by_id(trace_id)
    if not row:
        raise HTTPException(status_code=404, detail="Trace not found")
    
    return TraceItem(
        id=row["id"], ts=row["ts"], method=row["method"], path=row["path"],
        status=row["status"], latency_ms=row["latency_ms"], ip=row["ip"], ua=row["ua"],
        headers_slim=(json.loads(row["headers_slim"]) if row["headers_slim"] else None),
        query=(json.loads(row["query"]) if row["query"] else None),
        body_sha256=row["body_sha256"], token_sub=row["token_sub"], error=row["error"]
    )

@app.get("/v1/metrics/summary", response_model=MetricsSummary, tags=["Observability"], include_in_schema=False)
async def metrics_summary(
    request: Request,
    auth: dict = Depends(get_current_auth),
    window_seconds: int = Query(3600, ge=60, le=24*3600)
):
    # Check if user has required scopes (API key users have full access)
    if auth.get("auth_method") == "jwt":
        scopes = auth.get("scopes", [])
        if "read:basic" not in scopes and "read:metrics" not in scopes:
            raise HTTPException(status_code=403, detail="insufficient permissions")
    
    data = app.state.db.metrics_summary(window_seconds=window_seconds)
    return data

@app.get("/admin/health/status", response_model=HealthStatus, tags=["Admin"], include_in_schema=False)
async def health_status(request: Request, auth: dict = Depends(get_current_auth)):
    """Get comprehensive health status."""
    uptime = time.time() - app.state.startup_time
    
    # Check database connectivity
    try:
        app.state.db.query("SELECT 1")
        db_status = "connected"
        status = "healthy"
    except Exception:
        db_status = "disconnected"
        status = "unhealthy"
    
    return HealthStatus(
        status=status,
        database=db_status,
        uptime_seconds=uptime,
        version=VERSION
    )

@app.get("/admin/metrics/stream", tags=["Admin"], include_in_schema=False)
async def metrics_stream(
    request: Request, 
    api_key: Optional[str] = Query(None),
    token: Optional[str] = Query(None)
):
    """Server-Sent Events stream for real-time metrics updates."""
    
    # Authenticate using query parameters (since SSE can't use custom headers)
    auth_valid = False
    if api_key and api_key == KBAI_API_TOKEN:
        auth_valid = True
    elif token:
        try:
            from .auth import decode_token
            claims = decode_token(token)
            # Simple validation - in production you'd want to check session validity
            if claims.get("sub"):
                auth_valid = True
        except Exception:
            pass
    
    if not auth_valid:
        raise HTTPException(status_code=401, detail="Invalid authentication for SSE")
    
    async def event_generator():
        """Generate SSE events with metrics data."""
        try:
            while True:
                # Get latest metrics
                try:
                    metrics_data = app.state.db.metrics_summary(window_seconds=300)  # 5 minute window
                    
                    # Get recent traces (last 10)
                    recent_traces = app.state.db.list_traces(
                        since=None, limit=10, status=None, path=None, ip=None
                    )
                    
                    traces_data = []
                    for r in recent_traces:
                        traces_data.append({
                            "id": r["id"],
                            "ts": r["ts"],
                            "method": r["method"],
                            "path": r["path"],
                            "status": r["status"],
                            "latency_ms": r["latency_ms"],
                            "ip": r["ip"],
                            "auth_method": "api_key" if r["token_sub"] == "api_key_auth" else "jwt"
                        })
                    
                    # Combine data
                    event_data = {
                        "metrics": metrics_data,
                        "recent_traces": traces_data,
                        "timestamp": time.time()
                    }
                    
                    yield f"data: {json.dumps(event_data)}\n\n"
                    
                except Exception as e:
                    error_data = {
                        "error": str(e),
                        "timestamp": time.time()
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                
                # Wait 5 seconds before next update
                await asyncio.sleep(5)
                
        except asyncio.CancelledError:
            print("SSE connection cancelled")
            return
        except Exception as e:
            print(f"SSE error: {e}")
            return
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

# Admin dashboard with no authentication requirement - handles auth in the frontend
@app.get("/admin", response_class=HTMLResponse, tags=["Admin"], include_in_schema=False)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request, "title": TITLE})

# Dashboard redirect (legacy support)
@app.get("/dashboard", response_class=HTMLResponse, tags=["Admin"], include_in_schema=False)
async def dashboard_redirect(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request, "title": TITLE})

# Root route - Enterprise Architecture Overview
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def architecture_overview(request: Request):
    """Enterprise architecture overview and system documentation."""
    return templates.TemplateResponse("index.html", {"request": request, "title": TITLE})

# Frontend interface for API interaction
@app.get("/frontend", response_class=HTMLResponse, include_in_schema=False)
async def frontend_interface(request: Request):
    """Interactive frontend interface for KBAI API."""
    return templates.TemplateResponse("frontend.html", {"request": request, "title": TITLE})

# Project endpoints
@app.post("/v1/projects", tags=["Projects"])
async def add_or_rename_project(project: Project, request: Request, auth: dict = Depends(get_current_auth)):
    mapping = _read_proj_map()
    is_new_project = project.id not in mapping
    mapping[project.id] = project
    _write_proj_map(mapping)
    _project_dir(project.id)  # Ensure directory exists
    
    # Initialize empty files for new projects
    if is_new_project:
        _init_project_files(project.id)
    
    return {"detail": "Project created/updated", "project": project}

@app.get("/v1/projects", response_model=List[Project], tags=["Projects"])
async def list_projects(request: Request, auth: dict = Depends(get_current_auth)):
    mapping = _read_proj_map()
    return list(mapping.values())

@app.get("/v1/projects/{project_id}", response_model=Project, tags=["Projects"])
async def get_project(project_id: str, request: Request, auth: dict = Depends(get_current_auth)):
    mapping = _read_proj_map()
    if project_id not in mapping:
        raise HTTPException(status_code=404, detail="Project not found")
    return mapping[project_id]

@app.delete("/v1/projects/{project_id}", tags=["Projects"])
async def delete_project(project_id: str, request: Request, auth: dict = Depends(get_current_auth)):
    mapping = _read_proj_map()
    if project_id not in mapping:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Remove project from mapping
    del mapping[project_id]
    _write_proj_map(mapping)
    
    # Remove the entire project directory from data/ folder
    project_dir = DATA_DIR / project_id
    if project_dir.exists():
        import shutil
        shutil.rmtree(project_dir)
    
    return {"detail": "Project deleted completely"}

@app.get("/v1/projects/{project_id}/faqs", response_model=List[FAQ], tags=["Projects"])
async def list_faqs(project_id: str, request: Request, auth: dict = Depends(get_current_auth)):
    project_dir = _project_dir(project_id)
    
    # Try to read from consolidated format first (AI Worker format)
    consolidated_file = project_dir / f"{project_id}.faq.json"
    if consolidated_file.exists():
        try:
            content = json.loads(consolidated_file.read_text(encoding="utf-8"))
            return [FAQ(**item) for item in content]
        except Exception:
            pass
    
    # Fall back to individual files format
    faqs_dir = project_dir / "faqs"
    items = _list_json(faqs_dir)
    return [FAQ(**item) for item in items]

@app.post("/v1/projects/{project_id}/faqs:batch_upsert", tags=["Projects"])
async def batch_upsert_faqs(project_id: str, req: BatchFAQUpsertRequest, request: Request, auth: dict = Depends(get_current_auth)):
    project_dir = _project_dir(project_id)
    faqs_dir = project_dir / "faqs"
    
    for faq in req.items:
        file_path = faqs_dir / f"{faq.id}.json"
        _write_json(file_path, faq.dict())
    
    return {"detail": f"Upserted {len(req.items)} FAQs"}

@app.delete("/v1/projects/{project_id}/faqs/{faq_id}", tags=["FAQs"])
async def delete_faq(project_id: str, faq_id: str, request: Request, auth: dict = Depends(get_current_auth)):
    """Delete a FAQ and trigger re-indexing."""
    if not app.state.ai_worker:
        # Fallback to simple file deletion
        project_dir = _project_dir(project_id)
        file_path = project_dir / "faqs" / f"{faq_id}.json"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="FAQ not found")
        _delete_json(file_path)
        return {"detail": "FAQ deleted"}
    
    try:
        response = await app.state.ai_worker.delete_faq(project_id, faq_id)
        
        if not response.success:
            if "not found" in response.message:
                raise HTTPException(status_code=404, detail=response.message)
            else:
                raise HTTPException(status_code=500, detail=response.message)
        
        # Log FAQ deletion
        app.state.db.add_trace_metadata(
            getattr(request.state, 'trace_id', None),
            {"faq_deleted": True, "project_id": project_id, "faq_id": faq_id, "index_rebuild_started": response.index_build_started}
        )
        
        return {
            "detail": response.message,
            "index_rebuild_started": response.index_build_started
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FAQ deletion failed: {str(e)}")

@app.get("/v1/projects/{project_id}/kb", response_model=List[KBArticle], tags=["Projects"])
async def list_kb(project_id: str, request: Request, auth: dict = Depends(get_current_auth)):
    project_dir = _project_dir(project_id)
    
    # Try to read from consolidated format first (AI Worker format)
    consolidated_file = project_dir / f"{project_id}.kb.json"
    if consolidated_file.exists():
        try:
            content = json.loads(consolidated_file.read_text(encoding="utf-8"))
            # Convert from KBEntry format (article) to KBArticle format (title)
            kb_articles = []
            for item in content:
                kb_data = item.copy()
                if 'article' in kb_data and 'title' not in kb_data:
                    kb_data['title'] = kb_data.pop('article')
                kb_articles.append(KBArticle(**kb_data))
            return kb_articles
        except Exception:
            pass
    
    # Fall back to individual files format
    kb_dir = project_dir / "kb"
    items = _list_json(kb_dir)
    return [KBArticle(**item) for item in items]

@app.post("/v1/projects/{project_id}/kb:batch_upsert", tags=["Projects"])
async def batch_upsert_kb(project_id: str, req: BatchKBUpsertRequest, request: Request, auth: dict = Depends(get_current_auth)):
    project_dir = _project_dir(project_id)
    kb_dir = project_dir / "kb"
    
    for kb in req.items:
        file_path = kb_dir / f"{kb.id}.json"
        _write_json(file_path, kb.dict())
    
    return {"detail": f"Upserted {len(req.items)} KB articles"}

@app.delete("/v1/projects/{project_id}/kb/{kb_id}", tags=["Knowledge Base"])
async def delete_kb(project_id: str, kb_id: str, request: Request, auth: dict = Depends(get_current_auth)):
    """Delete a KB article and trigger re-indexing."""
    if not app.state.ai_worker:
        # Fallback to simple file deletion
        project_dir = _project_dir(project_id)
        file_path = project_dir / "kb" / f"{kb_id}.json"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="KB article not found")
        _delete_json(file_path)
        return {"detail": "KB article deleted"}
    
    try:
        response = await app.state.ai_worker.delete_kb_article(project_id, kb_id)
        
        if not response.success:
            if "not found" in response.message:
                raise HTTPException(status_code=404, detail=response.message)
            else:
                raise HTTPException(status_code=500, detail=response.message)
        
        # Log KB deletion
        app.state.db.add_trace_metadata(
            getattr(request.state, 'trace_id', None),
            {"kb_deleted": True, "project_id": project_id, "kb_id": kb_id, "index_rebuild_started": response.index_build_started}
        )
        
        return {
            "detail": response.message,
            "index_rebuild_started": response.index_build_started
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KB article deletion failed: {str(e)}")

@app.post("/v1/projects/{project_id}/ingest", tags=["Projects"])
async def ingest_data(project_id: str, request: Request, file: UploadFile = File(...), auth: dict = Depends(get_current_auth)):
    project_dir = _project_dir(project_id)
    ingest_dir = project_dir / "ingest"
    
    # Save uploaded file
    file_path = ingest_dir / file.filename
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    return {"detail": f"File '{file.filename}' uploaded successfully", "size": len(content)}

# Mock endpoints removed - replaced with real AI-powered implementations below

# AI-Powered Query Endpoint
@app.post("/v1/query", response_model=AIQueryResponse, tags=["AI Query"])
async def query_ai(req: AIQueryRequest, request: Request, auth: dict = Depends(get_current_auth)):
    """AI-powered query processing with knowledge base search and sources."""
    if not app.state.ai_worker:
        raise HTTPException(status_code=503, detail="AI Worker not available")
    
    try:
        response = await app.state.ai_worker.answer_question(req.project_id, req.question)
        
        # Log query to traces
        app.state.db.add_trace_metadata(
            getattr(request.state, 'trace_id', None),
            {"query_project": req.project_id, "query_length": len(req.question), "sources_found": len(response.sources)}
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

# Document Upload and Processing
@app.post("/v1/projects/{project_id}/documents", response_model=DocumentUploadResponse, tags=["Documents"])
async def upload_document(
    project_id: str,
    file: UploadFile = File(..., description="Document file (PDF or DOCX)"),
    article_title: Optional[str] = Form(None, description="Optional article title"),
    request: Request = None,
    auth: dict = Depends(get_current_auth)
) -> DocumentUploadResponse:
    """Upload and process a document for ingestion into the knowledge base."""
    if not app.state.ai_worker:
        raise HTTPException(status_code=503, detail="AI Worker not available")
    
    try:
        response = await app.state.ai_worker.ingest_document(project_id, file, article_title)
        
        # Log document upload
        app.state.db.add_trace_metadata(
            getattr(request.state, 'trace_id', None),
            {"document_upload": True, "filename": file.filename, "project_id": project_id}
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")

# FAQ Management
@app.post("/v1/projects/{project_id}/faqs/add", response_model=DocumentUploadResponse, tags=["FAQs"])
async def add_faq(
    project_id: str,
    faq_request: FAQCreateRequest,
    request: Request,
    auth: dict = Depends(get_current_auth)
) -> DocumentUploadResponse:
    """Add a new FAQ entry to the project."""
    if not app.state.ai_worker:
        raise HTTPException(status_code=503, detail="AI Worker not available")
    
    try:
        response = await app.state.ai_worker.add_faq(project_id, faq_request.question, faq_request.answer)
        
        # Log FAQ addition
        app.state.db.add_trace_metadata(
            getattr(request.state, 'trace_id', None),
            {"faq_added": True, "project_id": project_id}
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FAQ creation failed: {str(e)}")

# KB Article Management
@app.post("/v1/projects/{project_id}/kb/add", response_model=DocumentUploadResponse, tags=["Knowledge Base"])
async def add_kb_article(
    project_id: str,
    kb_request: KBArticleCreateRequest,
    request: Request,
    auth: dict = Depends(get_current_auth)
) -> DocumentUploadResponse:
    """Add a new KB article entry to the project."""
    if not app.state.ai_worker:
        raise HTTPException(status_code=503, detail="AI Worker not available")
    
    try:
        response = await app.state.ai_worker.add_kb_article(project_id, kb_request.title, kb_request.content)
        
        # Log KB article addition
        app.state.db.add_trace_metadata(
            getattr(request.state, 'trace_id', None),
            {"kb_article_added": True, "project_id": project_id}
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KB article creation failed: {str(e)}")

# Index Management
@app.post("/v1/projects/{project_id}/rebuild-indexes", response_model=IndexBuildResponse, tags=["Indexes"])
async def rebuild_indexes(
    project_id: str,
    request: Request,
    auth: dict = Depends(get_current_auth)
) -> IndexBuildResponse:
    """Manually trigger index rebuild for a project."""
    if not app.state.ai_worker:
        raise HTTPException(status_code=503, detail="AI Worker not available")
    
    try:
        response = await app.state.ai_worker.rebuild_indexes(project_id)
        
        # Log index rebuild
        app.state.db.add_trace_metadata(
            getattr(request.state, 'trace_id', None),
            {"index_rebuild": True, "project_id": project_id}
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index rebuild failed: {str(e)}")

@app.get("/v1/projects/{project_id}/build-status", response_model=IndexBuildResponse, tags=["Indexes"])
async def get_build_status(
    project_id: str,
    request: Request,
    auth: dict = Depends(get_current_auth)
) -> IndexBuildResponse:
    """Get current index build status for a project."""
    if not app.state.ai_worker:
        raise HTTPException(status_code=503, detail="AI Worker not available")
    
    try:
        return await app.state.ai_worker.get_build_status(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get build status: {str(e)}")

# Enhanced FAQ/KB Access with File Download
@app.get("/v1/projects/{project_id}/faqs/{faq_id}", tags=["FAQs"])
async def get_faq_with_file(
    project_id: str,
    faq_id: str,
    request: Request,
    auth: dict = Depends(get_current_auth)
):
    """Get FAQ by ID, returns attachment file if available, otherwise JSON."""
    if not app.state.ai_worker:
        raise HTTPException(status_code=503, detail="AI Worker not available")
    
    try:
        # Check for attachment file first
        attachment_file = Path(app.state.ai_worker.base_dir) / project_id / "attachments" / f"{faq_id}-faq.txt"
        if attachment_file.exists():
            return FileResponse(
                path=str(attachment_file),
                media_type="text/plain",
                filename=f"{faq_id}-faq.txt"
            )
        
        # Fall back to JSON
        faq = app.state.ai_worker.get_faq_by_id(project_id, faq_id)
        if not faq:
            raise HTTPException(status_code=404, detail="FAQ not found")
        
        return faq.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get FAQ: {str(e)}")

@app.get("/v1/projects/{project_id}/kb/{kb_id}", tags=["Knowledge Base"])
async def get_kb_with_file(
    project_id: str,
    kb_id: str,
    request: Request,
    auth: dict = Depends(get_current_auth)
):
    """Get KB entry by ID, returns attachment file if available, otherwise JSON."""
    if not app.state.ai_worker:
        raise HTTPException(status_code=503, detail="AI Worker not available")
    
    try:
        # First get the KB entry to check for source_file
        kb = app.state.ai_worker.get_kb_by_id(project_id, kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail="KB entry not found")
        
        # Check if there's an associated attachment file
        if kb.source_file:
            attachments_dir = Path(app.state.ai_worker.base_dir) / project_id / "attachments"
            attachment_file = attachments_dir / kb.source_file
            
            if attachment_file.exists():
                # Determine media type
                media_type, _ = mimetypes.guess_type(str(attachment_file))
                if not media_type:
                    media_type = "application/octet-stream"
                
                return FileResponse(
                    path=str(attachment_file),
                    media_type=media_type,
                    filename=attachment_file.name
                )
        
        # Check for legacy attachment files (multiple possible extensions)
        attachments_dir = Path(app.state.ai_worker.base_dir) / project_id / "attachments"
        possible_files = [
            attachments_dir / f"{kb_id}-kb.txt",
            attachments_dir / f"{kb_id}-kb.docx", 
            attachments_dir / f"{kb_id}-kb.pdf"
        ]
        
        for attachment_file in possible_files:
            if attachment_file.exists():
                # Determine media type
                media_type, _ = mimetypes.guess_type(str(attachment_file))
                if not media_type:
                    media_type = "application/octet-stream"
                
                return FileResponse(
                    path=str(attachment_file),
                    media_type=media_type,
                    filename=attachment_file.name
                )
        
        # Fall back to JSON
        return kb.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get KB entry: {str(e)}")

# Tools endpoints
@app.get("/v1/tools", tags=["Tools"])
async def list_tools(request: Request, auth: dict = Depends(get_current_auth)):
    """List available AI tools."""
    if not app.state.ai_worker:
        raise HTTPException(status_code=503, detail="AI Worker not available")
    
    try:
        return {"tools": app.state.ai_worker.tool_manager.list_tools()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")

@app.post("/v1/tools/{tool_name}", tags=["Tools"])
async def execute_tool(
    tool_name: str,
    parameters: Dict[str, Any] = {},
    request: Request = None,
    auth: dict = Depends(get_current_auth)
):
    """Execute a specific tool with given parameters."""
    if not app.state.ai_worker:
        raise HTTPException(status_code=503, detail="AI Worker not available")
    
    try:
        result = await app.state.ai_worker.tool_manager.execute_tool(tool_name, **parameters)
        
        # Log tool execution
        app.state.db.add_trace_metadata(
            getattr(request.state, 'trace_id', None),
            {"tool_executed": tool_name, "tool_success": result.success}
        )
        
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")

# Legacy reindex endpoint (now with real implementation)
@app.post("/v1/projects/{project_id}/reindex", tags=["Projects"])
async def reindex(project_id: str, request: Request, auth: dict = Depends(get_current_auth)):
    """Trigger reindexing for a project (alias for rebuild-indexes)."""
    return await rebuild_indexes(project_id, request, auth)

@app.get("/v1/projects/{project_id}/stats", tags=["Projects"])
async def project_stats(project_id: str, request: Request, auth: dict = Depends(get_current_auth)):
    project_dir = _project_dir(project_id)
    
    faqs_count = len(list((project_dir / "faqs").glob("*.json")))
    kb_count = len(list((project_dir / "kb").glob("*.json")))
    ingest_count = len(list((project_dir / "ingest").iterdir()))
    
    return {
        "project_id": project_id,
        "faqs_count": faqs_count,
        "kb_articles_count": kb_count,
        "ingested_files_count": ingest_count
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), reload=False)