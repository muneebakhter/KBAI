from __future__ import annotations
import os, time, uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from .storage import DB

ALGORITHM = os.getenv("AUTH_JWT_ALG","HS256")
SIGNING_KEY = os.getenv("AUTH_SIGNING_KEY","dev-signing-key-change-me")
DEFAULT_TTL = int(os.getenv("AUTH_DEFAULT_TTL_SECONDS","3600"))

security = HTTPBearer(auto_error=False)

class Session(BaseModel):
    id: str
    jti: str
    client_name: str
    scopes: List[str]
    issued_at: datetime
    expires_at: datetime
    ip_lock: Optional[str] = None

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def make_session(client_name: str, scopes: List[str], ttl_seconds: Optional[int], ip_lock: Optional[str]) -> Session:
    issued = now_utc()
    ttl = ttl_seconds or DEFAULT_TTL
    return Session(
        id=f"sess_{uuid.uuid4().hex[:24]}",
        jti=f"jti_{uuid.uuid4().hex[:24]}",
        client_name=client_name,
        scopes=scopes,
        issued_at=issued,
        expires_at=issued + timedelta(seconds=ttl),
        ip_lock=ip_lock
    )

def issue_token(db: DB, sess: Session) -> Dict[str, Any]:
    claims = {
        "sub": sess.id,
        "jti": sess.jti,
        "client_name": sess.client_name,
        "scopes": sess.scopes,
        "iat": int(sess.issued_at.timestamp()),
        "exp": int(sess.expires_at.timestamp()),
    }
    token = jwt.encode(claims, SIGNING_KEY, algorithm=ALGORITHM)
    # persist session
    db.create_session(
        id=sess.id,
        jti=sess.jti,
        client_name=sess.client_name,
        scopes_csv=",".join(sess.scopes),
        issued_at=sess.issued_at.isoformat(),
        expires_at=sess.expires_at.isoformat(),
        ip_lock=sess.ip_lock
    )
    return {"token": token, "expires_at": sess.expires_at, "session_id": sess.id}

def authenticate_user(username: str, password: str) -> bool:
    """Simple authentication - in production this would check against a real user database"""
    return username == "admin" and password == "admin"

def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, SIGNING_KEY, algorithms=[ALGORITHM])

async def get_current_session(request: Request, credentials: Optional[HTTPAuthorizationCredentials]=Depends(security)) -> Dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing or invalid token")
    token = credentials.credentials
    try:
        claims = decode_token(token)
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    # session lookup
    sess_id = claims.get("sub")
    jti = claims.get("jti")
    if not sess_id or not jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token claims")
    
    # Get DB from request app state
    db = request.app.state.db
    row = db.get_session_by_id(sess_id)
    if not row or int(row["disabled"]) == 1:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="session disabled")
    # expiry
    exp = claims.get("exp")
    if exp and int(exp) < int(time.time()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token expired")
    # ip lock (simple exact match if present)
    ip_lock = row["ip_lock"]
    client_ip = request.headers.get("x-forwarded-for") or request.client.host
    if ip_lock and client_ip != ip_lock:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ip not allowed for session")
    # store on request state for tracing
    request.state.session_id = sess_id
    request.state.session_scopes = (row["scopes"] or "").split(",")
    return {"session_id": sess_id, "scopes": request.state.session_scopes}

def require_scopes(required: List[str]):
    async def _dep(request: Request):
        scopes = getattr(request.state, "session_scopes", None)
        if scopes is None:
            raise HTTPException(status_code=401, detail="unauthorized")
        missing = [s for s in required if s not in scopes]
        if missing:
            raise HTTPException(status_code=403, detail=f"missing scopes: {','.join(missing)}")
        return True
    return _dep