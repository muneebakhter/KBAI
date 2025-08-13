from __future__ import annotations
import time, hashlib, json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from .storage import DB

SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key"}

def _scrub_headers(headers):
    out = {}
    for k, v in headers.items():
        lk = k.lower()
        if lk in SENSITIVE_HEADERS:
            continue
        out[lk] = v if len(v) <= 200 else (v[:200] + "...")
    return out

def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    xri = request.headers.get("x-real-ip")
    if xri:
        return xri
    return request.client.host if request.client else "unknown"

class TraceMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, db: DB, max_request_bytes: int = 65536):
        super().__init__(app)
        self.db = db
        self.max_request_bytes = max_request_bytes

    async def dispatch(self, request: Request, call_next: Callable):
        start = time.perf_counter()
        # read and cap body
        try:
            body = await request.body()
            if body and len(body) > self.max_request_bytes:
                # Cap: return 413 but still trace
                body_hash = hashlib.sha256(body[:self.max_request_bytes]).hexdigest()
                status_code = 413
                response = Response(content=json.dumps({"error":"payload_too_large","message":"request exceeds size limit"}),
                                    status_code=status_code, media_type="application/json")
                # trace
                await self._trace(request, response, start, body_hash, error="payload too large")
                return response
        except Exception:
            body = b""
        body_hash = hashlib.sha256(body).hexdigest() if body else None

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # 500 path
            status_code = 500
            response = Response(content=json.dumps({"error":"internal","message":"unhandled error"}),
                                status_code=status_code, media_type="application/json")
            await self._trace(request, response, start, body_hash, error=str(e))
            return response

        await self._trace(request, response, start, body_hash)
        return response

    async def _trace(self, request: Request, response: Response, start: float, body_hash: str|None, error: str|None=None):
        dur_ms = (time.perf_counter() - start) * 1000.0
        # gather
        ip = _client_ip(request)
        ua = request.headers.get("user-agent")
        headers_slim = _scrub_headers(request.headers)
        # query params
        query = dict(request.query_params.multi_items())
        # session id (if any)
        token_sub = getattr(request.state, "session_id", None)
        # id + ts
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).isoformat()
        trace_id = f"tr_{hashlib.md5((ts+request.url.path+ip).encode()).hexdigest()[:24]}"
        # store
        self.db.insert_trace({
            "id": trace_id,
            "ts": ts,
            "method": request.method,
            "path": request.url.path,
            "status": int(response.status_code),
            "latency_ms": float(dur_ms),
            "ip": ip,
            "ua": ua,
            "headers_slim": json.dumps(headers_slim),
            "query": json.dumps(query),
            "body_sha256": body_hash,
            "token_sub": token_sub,
            "error": error
        })