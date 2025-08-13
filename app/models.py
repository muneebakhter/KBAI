from __future__ import annotations
from pydantic import BaseModel, Field, conlist, constr
from typing import List, Optional
from datetime import datetime

class TokenRequest(BaseModel):
    username: str = Field(..., description="Username for authentication")
    password: str = Field(..., description="Password for authentication")
    client_name: str = Field(default="kbai-client", description="Client identifier")
    scopes: List[str] = Field(default=["read:basic"], description="Requested scopes")
    ttl_seconds: int = Field(default=3600, description="Token time to live in seconds")

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_at: datetime = Field(..., description="Token expiration time")
    session_id: str = Field(..., description="Session identifier")

class TraceItem(BaseModel):
    id: str
    ts: str
    method: str
    path: str
    status: int
    latency_ms: float
    ip: Optional[str] = None
    ua: Optional[str] = None
    headers_slim: Optional[dict] = None
    query: Optional[dict] = None
    body_sha256: Optional[str] = None
    token_sub: Optional[str] = None
    error: Optional[str] = None

class TracesResponse(BaseModel):
    items: List[TraceItem]
    next_cursor: Optional[str] = None

class MetricsSummary(BaseModel):
    window: str
    total: int
    by_status: dict
    top_paths: list
    unauthorized: int
    p95_latency_ms: Optional[float] = None

# Existing models from the original app
class Project(BaseModel):
    id: str = Field(..., description="Project identifier")
    name: str = Field(..., description="Human-readable name")
    active: bool = True

class FAQ(BaseModel):
    id: str
    question: str
    answer: str

class KBArticle(BaseModel):
    id: str
    title: str
    content: str
    source: Optional[str] = None
    source_file: Optional[str] = None
    chunk_index: Optional[int] = None

class BatchFAQUpsertRequest(BaseModel):
    items: List[FAQ]

class BatchKBUpsertRequest(BaseModel):
    items: List[KBArticle]

class QueryRequest(BaseModel):
    project_id: str
    question: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[str] = []

class AuthModes(BaseModel):
    jwt_enabled: bool = True
    api_key_enabled: bool = True
    api_key_configured: bool

class HealthStatus(BaseModel):
    status: str = "healthy"
    database: str = "connected" 
    uptime_seconds: Optional[float] = None
    version: str = "1.0.0"